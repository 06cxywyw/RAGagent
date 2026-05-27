package com.example.rag;

import com.example.rag.rag.HybridRetriever;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.core.io.ClassPathResource;
import org.springframework.util.StringUtils;

import java.util.*;

@Slf4j
public final class GoldenEvaluationSupport {

    private GoldenEvaluationSupport() {
    }

    private static final ObjectMapper MAPPER = new ObjectMapper()
            .setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);

    @Data
    public static class TestCase {
        private String category;
        private String question;
        private String expectedSnippet;
    }

    @Data
    public static class EvalConfig {
        private int maxK;
        private boolean rewrite;
        private boolean fts;
        private boolean vector;
        private boolean rerank;

        public static EvalConfig of(int maxK, boolean rewrite, boolean fts, boolean vector, boolean rerank) {
            EvalConfig c = new EvalConfig();
            c.maxK = maxK;
            c.rewrite = rewrite;
            c.fts = fts;
            c.vector = vector;
            c.rerank = rerank;
            return c;
        }
    }

    @Data
    public static class EvalResult {
        private int total;
        private double mrr;
        private Map<Integer, Double> recallAtK = new LinkedHashMap<>();
        private Map<Integer, Double> hitRateAtK = new LinkedHashMap<>();
        private Map<Integer, Double> ndcgAtK = new LinkedHashMap<>();
    }

    public static List<TestCase> loadCases(String classpathJson) throws Exception {
        return MAPPER.readValue(
                new ClassPathResource(classpathJson).getInputStream(),
                new TypeReference<List<TestCase>>() {
                }
        );
    }

    public static EvalResult evaluate(
            HybridRetriever hybridRetriever,
            List<TestCase> testCases,
            EvalConfig config,
            int[] ks
    ) {
        Objects.requireNonNull(hybridRetriever, "hybridRetriever");
        Objects.requireNonNull(testCases, "testCases");

        int total = testCases.size();
        int maxK = config.getMaxK();

        Map<Integer, Integer> hitsAtK = new LinkedHashMap<>();
        Map<Integer, Double> ndcgAtK = new LinkedHashMap<>();
        Map<Integer, Double> recallAtK = new LinkedHashMap<>();

        for (int k : ks) {
            hitsAtK.put(k, 0);
            ndcgAtK.put(k, 0.0);
            recallAtK.put(k, 0.0);
        }

        double mrrSum = 0.0;

        for (TestCase tc : testCases) {
            List<Document> results;
            try {
                results = hybridRetriever.retrieve(tc.getQuestion(), maxK,
                        config.isRewrite(), config.isFts(), config.isVector(), config.isRerank());
            } catch (Exception e) {
                log.warn("检索异常: category={}, err={}", tc.getCategory(), e.getMessage());
                results = Collections.emptyList();
            }

            List<Integer> rel = relevanceList(results, tc.getExpectedSnippet(), maxK);

            int first = firstRelevantRank(rel);
            if (first > 0) {
                mrrSum += 1.0 / first;
            }

            for (int k : ks) {
                List<Integer> relAtK = rel.subList(0, Math.min(k, rel.size()));
                boolean hit = relAtK.stream().anyMatch(x -> x == 1);
                if (hit) {
                    hitsAtK.put(k, hitsAtK.get(k) + 1);
                }

                // 单相关文档假设：totalRelevant=1
                int foundRelevant = (int) relAtK.stream().filter(x -> x == 1).count();
                recallAtK.put(k, recallAtK.get(k) + Math.min(foundRelevant, 1));

                double ndcg = calcNdcgBinary(relAtK, 1);
                ndcgAtK.put(k, ndcgAtK.get(k) + ndcg);
            }
        }

        EvalResult out = new EvalResult();
        out.setTotal(total);
        out.setMrr(mrrSum / total);

        for (int k : ks) {
            out.getRecallAtK().put(k, recallAtK.get(k) / total);
            out.getHitRateAtK().put(k, hitsAtK.get(k) * 1.0 / total);
            out.getNdcgAtK().put(k, ndcgAtK.get(k) / total);
        }

        return out;
    }

    public static void printReport(String title, EvalConfig config, EvalResult result, int[] ks) {
        System.out.println("\n" + "=".repeat(100));
        System.out.println("  " + title);
        System.out.println("  样本数: " + result.getTotal() + " | topK: " + config.getMaxK() + " | 日期: " + new Date());
        System.out.println("  配置: rewrite=" + config.isRewrite()
                + ", fts=" + config.isFts()
                + ", vector=" + config.isVector()
                + ", rerank=" + config.isRerank());
        System.out.println("  相关性: text contains expected_snippet");
        System.out.println("=".repeat(100));

        System.out.printf("\n  1) MRR = %.4f\n", result.getMrr());

        System.out.println("\n  2) Recall@k / HitRate@k / mDCG@k(nDCG@k)");
        System.out.println("     " + "-".repeat(72));
        System.out.printf("     %-8s %-14s %-14s %-14s\n", "k", "Recall@k", "HitRate@k", "mDCG@k(nDCG@k)");
        System.out.println("     " + "-".repeat(72));

        for (int k : ks) {
            System.out.printf("     %-8s %-14.4f %-14.4f %-14.4f\n",
                    "k=" + k,
                    result.getRecallAtK().get(k),
                    result.getHitRateAtK().get(k),
                    result.getNdcgAtK().get(k));
        }
        System.out.println("     " + "-".repeat(72));
    }

    private static List<Integer> relevanceList(List<Document> results, String expectedSnippet, int maxK) {
        List<Integer> rel = new ArrayList<>(maxK);
        for (int i = 0; i < maxK; i++) {
            if (i >= results.size()) {
                rel.add(0);
                continue;
            }
            String text = results.get(i).getText();
            rel.add(isRelevant(text, expectedSnippet) ? 1 : 0);
        }
        return rel;
    }

    private static boolean isRelevant(String text, String expectedSnippet) {
        if (!StringUtils.hasText(text) || !StringUtils.hasText(expectedSnippet)) {
            return false;
        }
        return text.contains(expectedSnippet);
    }

    private static int firstRelevantRank(List<Integer> rel) {
        for (int i = 0; i < rel.size(); i++) {
            if (rel.get(i) == 1) {
                return i + 1;
            }
        }
        return -1;
    }

    private static double calcNdcgBinary(List<Integer> relAtK, int totalRelevant) {
        if (totalRelevant <= 0) return 0.0;

        double dcg = 0.0;
        for (int i = 0; i < relAtK.size(); i++) {
            int r = relAtK.get(i);
            if (r == 0) continue;
            int rank = i + 1;
            dcg += 1.0 / (Math.log(rank + 1) / Math.log(2));
        }

        int idealCount = Math.min(totalRelevant, relAtK.size());
        double idcg = 0.0;
        for (int i = 0; i < idealCount; i++) {
            int rank = i + 1;
            idcg += 1.0 / (Math.log(rank + 1) / Math.log(2));
        }

        return idcg > 0 ? (dcg / idcg) : 0.0;
    }
}

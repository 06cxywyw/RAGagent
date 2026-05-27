package com.example.rag;

import com.example.rag.rag.HybridRetriever;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import jakarta.annotation.Resource;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.springframework.ai.document.Document;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.io.ClassPathResource;
import org.springframework.test.context.ActiveProfiles;

import java.util.*;

/**
 * 黄金 50 检索评测：Recall@k / HitRate@k / MRR / nDCG@k
 *
 * 数据集：src/test/resources/rag_golden_50.json
 * 相关性判定：检索结果文本包含 expected_snippet 即视为 relevant
 */
@Slf4j
@SpringBootTest
@ActiveProfiles("dev")
public class RagGolden50EvaluationTest {

    @Resource
    private HybridRetriever hybridRetriever;

    private static final ObjectMapper MAPPER = new ObjectMapper()
            .setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);

    private static List<TestCase> testCases;

    @Data
    static class TestCase {
        private String category;
        private String question;
        private String expectedSnippet;
    }

    @BeforeAll
    static void load() throws Exception {
        testCases = MAPPER.readValue(
                new ClassPathResource("rag_golden_50.json").getInputStream(),
                new TypeReference<List<TestCase>>() {}
        );
        System.out.println("加载黄金测试用例: " + testCases.size() + " 条");
    }

    @Test
    void evaluateGolden50() {
        int total = testCases.size();
        int maxK = Integer.parseInt(System.getProperty("rag.eval.maxK", "10"));

        boolean doRewrite = Boolean.parseBoolean(System.getProperty("rag.eval.rewrite", "true"));
        boolean doFts = Boolean.parseBoolean(System.getProperty("rag.eval.fts", "true"));
        boolean doVector = Boolean.parseBoolean(System.getProperty("rag.eval.vector", "true"));
        // 默认开启：全链路评测（如需更快/省成本，可通过 VM 参数关闭）
        boolean doRerank = Boolean.parseBoolean(System.getProperty("rag.eval.rerank", "true"));

        int[] ks = {1, 3, 5, 10};
        Map<Integer, Integer> hitsAtK = new LinkedHashMap<>();
        Map<Integer, Double> ndcgAtK = new LinkedHashMap<>();
        Map<Integer, Double> recallAtK = new LinkedHashMap<>();
        for (int k : ks) {
            hitsAtK.put(k, 0);
            ndcgAtK.put(k, 0.0);
            recallAtK.put(k, 0.0);
        }

        double mrrSum = 0.0;

        // 为了避免重复检索，先对每个 query 拉满 top-10，再切片算各 k
        for (TestCase tc : testCases) {
            List<Document> results;
            try {
                results = hybridRetriever.retrieve(tc.getQuestion(), maxK, doRewrite, doFts, doVector, doRerank);
            } catch (Exception e) {
                log.warn("检索异常: category={}, err={}", tc.getCategory(), e.getMessage());
                results = Collections.emptyList();
            }

            List<Integer> rel = relevanceList(results, tc.getExpectedSnippet(), maxK);

            // first relevant rank (1-based)
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

        double mrr = mrrSum / total;

        System.out.println("\n" + "=".repeat(100));
        System.out.println("  黄金50 检索评测报告");
        System.out.println("  样本数: " + total + " | topK: " + maxK + " | 日期: " + new Date());
        System.out.println("  配置: rewrite=" + doRewrite + ", fts=" + doFts + ", vector=" + doVector + ", rerank=" + doRerank);
        System.out.println("  相关性: text contains expected_snippet");
        System.out.println("=".repeat(100));

        System.out.printf("\n  1) MRR = %.4f\n", mrr);

        System.out.println("\n  2) Recall@k / HitRate@k / nDCG@k");
        System.out.println("     " + "-".repeat(72));
        System.out.printf("     %-8s %-14s %-14s %-14s\n", "k", "Recall@k", "HitRate@k", "mDCG@k(nDCG@k)");
        System.out.println("     " + "-".repeat(72));

        for (int k : ks) {
            double recall = recallAtK.get(k) / total;
            double hitRate = hitsAtK.get(k) * 1.0 / total;
            double ndcg = ndcgAtK.get(k) / total;
            System.out.printf("     %-8s %-14.4f %-14.4f %-14.4f\n", "k=" + k, recall, hitRate, ndcg);
        }
        System.out.println("     " + "-".repeat(72));

        System.out.println("\n  说明：");
        System.out.println("  - Recall@k：相关文档在 top-k 中被找回的比例（本数据集每题默认 1 条相关）");
        System.out.println("  - HitRate@k：top-k 内至少命中 1 次的比例（单相关时与 Recall@k 接近）");
        System.out.println("  - nDCG@k：考虑排名位置的指标，越靠前命中得分越高");
        System.out.println("  - MRR：首个命中的倒数排名均值，越接近 1 越好\n");
    }

    private static List<Integer> relevanceList(List<Document> results, String expectedSnippet, int maxK) {
        List<Integer> rel = new ArrayList<>(maxK);
        for (int i = 0; i < maxK; i++) {
            if (i >= results.size()) {
                rel.add(0);
                continue;
            }
            String text = results.get(i).getText();
            rel.add(text != null && expectedSnippet != null && !expectedSnippet.isBlank() && text.contains(expectedSnippet) ? 1 : 0);
        }
        return rel;
    }

    private static int firstRelevantRank(List<Integer> rel) {
        for (int i = 0; i < rel.size(); i++) {
            if (rel.get(i) == 1) {
                return i + 1; // 1-based
            }
        }
        return -1;
    }

    /**
     * nDCG@k for binary relevance.
     * totalRelevant: 本 query 的相关文档总数（这里通常为 1）
     */
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

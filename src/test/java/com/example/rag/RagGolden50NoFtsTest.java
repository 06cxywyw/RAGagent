package com.example.rag;

import com.example.rag.rag.HybridRetriever;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;

@Slf4j
@SpringBootTest
@ActiveProfiles("dev")
public class RagGolden50NoFtsTest {

    @Resource
    private HybridRetriever hybridRetriever;

    private static List<GoldenEvaluationSupport.TestCase> testCases;

    @BeforeAll
    static void load() throws Exception {
        testCases = GoldenEvaluationSupport.loadCases("rag_golden_50.json");
        System.out.println("加载黄金测试用例: " + testCases.size() + " 条");
    }

    @Test
    void evaluate_noFts() {
        int maxK = Integer.parseInt(System.getProperty("rag.eval.maxK", "10"));
        boolean doRewrite = Boolean.parseBoolean(System.getProperty("rag.eval.rewrite", "true"));
        boolean doVector = Boolean.parseBoolean(System.getProperty("rag.eval.vector", "true"));
        boolean doRerank = Boolean.parseBoolean(System.getProperty("rag.eval.rerank", "true"));
        int[] ks = {1, 3, 5, 10};

        // 禁用 FTS，其余保持开启（全链路对照）
        GoldenEvaluationSupport.EvalConfig cfg = GoldenEvaluationSupport.EvalConfig.of(
                maxK,
            doRewrite,   // rewrite
                false,  // fts
            doVector,   // vector
            doRerank    // rerank
        );

        GoldenEvaluationSupport.EvalResult r = GoldenEvaluationSupport.evaluate(hybridRetriever, testCases, cfg, ks);
        GoldenEvaluationSupport.printReport("黄金50 单测：禁用 FTS 全文检索", cfg, r, ks);
    }
}

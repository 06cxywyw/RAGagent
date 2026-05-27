package com.example.rag;

import com.example.rag.rag.IngestionService;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

/**
 * 手动入库测试类
 *
 * 在 IntelliJ 中运行具体方法即可触发入库：
 *   - ingestXiaolincoding() → 入库小林coding 文档
 *   - ingestJavaguide()     → 入库 JavaGuide 文档
 *   - ingestAll()           → 入库全部文档
 */
@Slf4j
@SpringBootTest
@ActiveProfiles("dev")
public class IngestionRunner {

    @Autowired
    private IngestionService ingestionService;

    @Test
    public void ingestXiaolincoding() {
        String result = ingestionService.ingest("xiaolincoding");
        System.out.println("\n" + "=".repeat(60));
        System.out.println(result);
        System.out.println("=".repeat(60));
    }

    @Test
    public void ingestJavaguide() {
        String result = ingestionService.ingest("javaguide");
        System.out.println("\n" + "=".repeat(60));
        System.out.println(result);
        System.out.println("=".repeat(60));
    }

    @Test
    public void ingestAll() {
        System.out.println("【xiaolincoding】");
        String r1 = ingestionService.ingest("xiaolincoding");
        System.out.println(r1);

        System.out.println("\n【javaguide】");
        String r2 = ingestionService.ingest("javaguide");
        System.out.println(r2);

        System.out.println("\n" + "=".repeat(60));
        System.out.println("全量入库完成");
        System.out.println("=".repeat(60));
    }
}
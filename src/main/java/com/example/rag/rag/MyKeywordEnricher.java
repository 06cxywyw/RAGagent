package com.example.rag.rag;

import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

/**
 * 元数据增强器 — 使用本地分词器提取关键词，无需 LLM 调用
 */
@Component
@Slf4j
public class MyKeywordEnricher {

    @Resource
    private ChineseTokenizer chineseTokenizer;

    public List<Document> enrichDocuments(List<Document> documents) {

        List<Document> result = new ArrayList<>();

        for (Document doc : documents) {
            String text = doc.getText();
            if (text == null || text.isEmpty()) {
                result.add(doc);
                continue;
            }

            // 使用本地分词器提取关键词，替代 LLM 调用
            List<String> keywords = chineseTokenizer.extractKeywords(text, 5);
            String joined = String.join("，", keywords);
            doc.getMetadata().put("keywords", joined);
            result.add(doc);
        }

        return result;
    }
}
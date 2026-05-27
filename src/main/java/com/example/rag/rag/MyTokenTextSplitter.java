package com.example.rag.rag;

import org.springframework.ai.document.Document;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * token切分器
 */
@Component
public class MyTokenTextSplitter {
    
    /**
     * 默认分割（不分割）
     */
    public List<Document> splitDocuments(List<Document> documents) {
        TokenTextSplitter splitter = new TokenTextSplitter();
        return splitter.apply(documents);
    }

    /**
     * 优化后的中文切片策略
     * 参数解释：
     * - 1000: chunk size (约2000-3000中文字符，保证上下文完整)
     * - 200: overlap (保证切片之间有连贯性)
     * - 10: min characters (最小字符数)
     * - 5000: max size (最大限制)
     * - true: keep separator (保留分隔符)
     */
    public List<Document> splitCustomized(List<Document> documents) {
        // 适配 bge-m3（支持 8192 tokens，chunk size 保持 1000）
        TokenTextSplitter splitter = new TokenTextSplitter(
            1000,   // chunk size
            200,    // overlap
            100,    // min characters
            5000,   // max size
            true    // keep separator
        );
        List<Document> split = splitter.apply(documents);

        // ⭐ 合并过小的相邻 chunk，避免碎片化
        return mergeSmallChunks(split, 200);
    }

    /**
     * 合并过小的相邻 chunk，保证每个 chunk 有最低信息量
     */
    private List<Document> mergeSmallChunks(List<Document> docs, int minLen) {
        List<Document> result = new java.util.ArrayList<>();
        Document current = null;
        for (Document doc : docs) {
            if (current == null) {
                current = doc;
                continue;
            }
            // 如果当前累积的 chunk 太小，合并
            if (current.getText().length() < minLen) {
                String merged = current.getText() + "\n" + doc.getText();
                Document mergedDoc = new Document(merged);
                mergedDoc.getMetadata().putAll(current.getMetadata());
                current = mergedDoc;
            } else {
                result.add(current);
                current = doc;
            }
        }
        if (current != null) result.add(current);
        return result;
    }
    
    /**
     * 激进分割（需要更细粒度时用）
     */
    public List<Document> splitAggressive(List<Document> documents) {
        TokenTextSplitter splitter = new TokenTextSplitter(
            500,     // 更小的chunk
            100,     // 更小的overlap
            5,       // 最小字符数
            2000,    // 最大限制
            true
        );
        return splitter.apply(documents);
    }
    
    /**
     * 保守分割（需要更大块时用）
     */
    public List<Document> splitConservative(List<Document> documents) {
        TokenTextSplitter splitter = new TokenTextSplitter(
            2000,    // 更大的chunk
            400,     // 更大的overlap
            20,      // 最小字符数
            8000,    // 最大限制
            true
        );
        return splitter.apply(documents);
    }
}


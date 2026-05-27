package com.example.rag.rag;

import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
public class IngestionService {

    private static final int MAX_CONTENT_CHARS = 2000;

    @Resource
    private MyKeywordEnricher myKeywordEnricher;

    @Resource
    private MyHashUtil myHashUtil;

    @Resource
    @Qualifier("pgVectorVectorStore")
    private VectorStore vectorStore;

    @Resource
    private JdbcTemplate jdbcTemplate;

    @Resource
    private LoveAppDocumentLoader loader;

    public String ingest(String subdirPattern) {
        long start = System.currentTimeMillis();
        StringBuilder report = new StringBuilder();

        try {
            boolean tableExists = true;
            try {
                jdbcTemplate.queryForObject("SELECT COUNT(*) FROM vector_store", Integer.class);
            } catch (Exception e) {
                tableExists = false;
            }

            List<Document> documents = loader.loadMarkdowns(subdirPattern);
            if (documents == null || documents.isEmpty()) {
                return "【" + subdirPattern + "】没有加载到文档";
            }
            report.append("原始文档数: ").append(documents.size()).append("\n");

            int before = documents.size();
            documents = myHashUtil.deduplicate(documents);
            report.append("去重: ").append(before).append(" → ").append(documents.size()).append("\n");

            if (tableExists) {
                List<String> hashList = documents.stream()
                        .map(doc -> (String) doc.getMetadata().get("hash"))
                        .toList();
                if (!hashList.isEmpty()) {
                    String inSql = String.join(",",
                            java.util.Collections.nCopies(hashList.size(), "?"));
                    List<String> existingHashes = jdbcTemplate.queryForList(
                            "SELECT metadata->>'hash' FROM vector_store WHERE metadata->>'hash' IN (" + inSql + ")",
                            String.class, hashList.toArray());
                    java.util.Set<String> existingSet = new java.util.HashSet<>(existingHashes);
                    int beforeFilter = documents.size();
                    documents = documents.stream()
                            .filter(doc -> !existingSet.contains(doc.getMetadata().get("hash")))
                            .toList();
                    report.append("幂等性过滤: ").append(beforeFilter).append(" → ").append(documents.size())
                            .append("（已存在").append(existingSet.size()).append("条）\n");
                    if (documents.isEmpty()) {
                        return report + "向量库已包含所有文档，跳过入库";
                    }
                }
            }

            int truncated = 0;
            List<Document> trimmed = new java.util.ArrayList<>();
            for (Document doc : documents) {
                String text = doc.getText();
                if (text.length() > MAX_CONTENT_CHARS) {
                    Document truncatedDoc = new Document(text.substring(0, MAX_CONTENT_CHARS));
                    truncatedDoc.getMetadata().putAll(doc.getMetadata());
                    trimmed.add(truncatedDoc);
                    truncated++;
                } else {
                    trimmed.add(doc);
                }
            }
            documents = trimmed;
            if (truncated > 0) {
                report.append("截断超长文档（>" + MAX_CONTENT_CHARS + "字符）: ").append(truncated).append(" 篇\n");
            }

            log.info("【{}】开始元数据增强...", subdirPattern);
            int enrichBatchSize = 100;
            List<Document> enrichedDocs = new java.util.ArrayList<>();
            for (int i = 0; i < documents.size(); i += enrichBatchSize) {
                int end = Math.min(i + enrichBatchSize, documents.size());
                enrichedDocs.addAll(myKeywordEnricher.enrichDocuments(documents.subList(i, end)));
            }
            documents = enrichedDocs;
            report.append("元数据增强完成\n");

            int batchSize = 10;
            int total = documents.size();
            int batchCount = (total + batchSize - 1) / batchSize;
            for (int i = 0; i < batchCount; i++) {
                int startIdx = i * batchSize;
                int end = Math.min(startIdx + batchSize, total);
                vectorStore.add(documents.subList(startIdx, end));
                log.info("【{}】批次 {}/{} 入库完成，数量: {}", subdirPattern, i + 1, batchCount, end - startIdx);
            }

            long elapsed = (System.currentTimeMillis() - start) / 1000;
            report.append("总入库: ").append(total).append(" 条\n");
            report.append("耗时: ").append(elapsed).append(" 秒\n");
            report.append("数据源: ").append(subdirPattern).append(" ✅");

        } catch (Exception e) {
            log.error("【{}】入库失败", subdirPattern, e);
            return "【" + subdirPattern + "】入库失败: " + e.getMessage();
        }
        return report.toString();
    }
}
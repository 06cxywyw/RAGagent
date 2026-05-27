package com.example.rag.rag;

import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Component
public class HybridRetriever {

    private static final int VECTOR_TOP_K = 15;
    private static final int FTS_TOP_K = 10;

    @Resource
    @Qualifier("pgVectorVectorStore")
    private VectorStore vectorStore;

    @Resource
    private JdbcTemplate jdbcTemplate;

    @Resource
    private Reranker reranker;

    @Resource
    private FullTextSearchRetriever fullTextSearchRetriever;

    @Resource
    private QueryRewriter queryRewriter;

    public List<Document> retrieve(String query) {
        return retrieve(query, 3);
    }

    public List<Document> retrieve(String query, int topK) {
        String rewritten = queryRewriter.rewrite(query);
        List<Document> keywordDocs = fullTextKeywordSearch(rewritten);
        List<Document> vectorDocs = vectorSearch(rewritten);
        List<Document> fused = fusion(keywordDocs, vectorDocs);
        List<Document> reranked = rerank(query, fused);
        return reranked.stream().limit(topK).collect(Collectors.toList());
    }

    /** A/B 测试：可开关各模块 */
    public List<Document> retrieve(String query, int topK, boolean doRewrite, boolean doFts, boolean doVector, boolean doRerank) {
        String searchQuery = doRewrite ? queryRewriter.rewrite(query) : query;

        List<Document> fts = doFts ? fullTextKeywordSearch(searchQuery) : Collections.emptyList();
        List<Document> vec = doVector ? vectorSearch(searchQuery) : Collections.emptyList();
        List<Document> fused = fusion(fts, vec);

        if (fused.isEmpty()) return Collections.emptyList();
        if (!doRerank || fused.size() <= 1) return fused.stream().limit(topK).collect(Collectors.toList());

        List<Document> reranked = reranker.rerank(query, fused);
        return reranked.stream().limit(topK).collect(Collectors.toList());
    }

    private List<Document> vectorSearch(String query) {
        List<Document> docs = vectorStore.similaritySearch(
                SearchRequest.builder().query(query).topK(VECTOR_TOP_K).build());
        for (Document doc : docs) doc.getMetadata().put("source", "vector");
        log.info("vector docs = {}", docs.size());
        return docs;
    }

    private List<Document> fullTextKeywordSearch(String query) {
        try {
            List<Document> docs = fullTextSearchRetriever.fullTextSearch(query, FTS_TOP_K);
            log.info("fulltext docs = {}", docs.size());
            return docs;
        } catch (Exception e) {
            log.warn("全文搜索失败", e);
            return Collections.emptyList();
        }
    }

    private List<Document> fusion(List<Document> keywordDocs, List<Document> vectorDocs) {
        List<Document> result = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        addDocs(result, seen, keywordDocs);
        addDocs(result, seen, vectorDocs);
        return result;
    }

    private void addDocs(List<Document> result, Set<String> seen, List<Document> docs) {
        for (Document doc : docs) {
            String id = resolveId(doc);
            if (seen.add(id)) result.add(doc);
        }
    }

    private String resolveId(Document doc) {
        Object hash = doc.getMetadata().get("hash");
        if (hash != null) return hash.toString();
        Object id = doc.getMetadata().get("id");
        if (id != null) return id.toString();
        return String.valueOf(doc.getText().hashCode());
    }

    private List<Document> rerank(String query, List<Document> docs) {
        if (docs.size() <= 1) return docs;
        return reranker.rerank(query, docs);
    }
}
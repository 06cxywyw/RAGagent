package com.example.rag.rag;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.HashMap;

import java.util.Collections;
import java.util.List;
import java.util.Map;

@Slf4j
@Component
public class FullTextSearchRetriever {

    @Resource
    private JdbcTemplate jdbcTemplate;

    @Resource
    private ObjectMapper objectMapper;

    /**
     * 全文搜索召回 — 使用 zhparser 中文分词
     */
    public List<Document> fullTextSearch(String query, int limit) {
        try {
            String sql = """
                SELECT id::text as id, content, metadata,
                       ts_rank(to_tsvector('zhcfg', content), plainto_tsquery('zhcfg', ?)) as rank
                FROM vector_store
                WHERE to_tsvector('zhcfg', content) @@ plainto_tsquery('zhcfg', ?)
                ORDER BY rank DESC
                LIMIT ?
                """;

            return jdbcTemplate.query(
                sql,
                new Object[]{query, query, limit},
                (rs, i) -> {
                    Document doc = new Document(rs.getString("content"));

                    String id = rs.getString("id");
                    if (id != null && !id.isBlank()) {
                        doc.getMetadata().put("id", id);
                    }

                    Map<String, Object> metadata = parseMetadata(rs.getObject("metadata"));
                    if (!metadata.isEmpty()) {
                        doc.getMetadata().putAll(metadata);
                    }

                    doc.getMetadata().put("source", "fulltext");
                    doc.getMetadata().put("rank", rs.getDouble("rank"));
                    return doc;
                }
            );

        } catch (Exception e) {
            log.error("全文搜索失败", e);
            return Collections.emptyList();
        }
    }

    private Map<String, Object> parseMetadata(Object raw) {
        if (raw == null) {
            return Map.of();
        }

        try {
            if (raw instanceof Map<?, ?> m) {
                Map<String, Object> result = new HashMap<>();
                for (Map.Entry<?, ?> e : m.entrySet()) {
                    if (e.getKey() != null) {
                        result.put(String.valueOf(e.getKey()), e.getValue());
                    }
                }
                return result;
            }

            String json;
            if (raw instanceof String s) {
                json = s;
            } else {
                // e.g. org.postgresql.util.PGobject
                try {
                    var getValue = raw.getClass().getMethod("getValue");
                    Object v = getValue.invoke(raw);
                    json = v == null ? null : v.toString();
                } catch (Exception reflectionFailure) {
                    json = raw.toString();
                }
            }

            if (json == null || json.isBlank() || "null".equalsIgnoreCase(json)) {
                return Map.of();
            }
            return objectMapper.readValue(json, new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            log.debug("解析 metadata 失败: {}", e.getMessage());
            return Map.of();
        }
    }
}
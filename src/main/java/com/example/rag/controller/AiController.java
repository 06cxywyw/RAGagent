package com.example.rag.controller;

import com.example.rag.rag.HybridRetriever;
import jakarta.annotation.Resource;
import org.springframework.ai.document.Document;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

import java.util.*;

@RestController
public class AiController {

    private static final int MAX_CONTEXT_CHARS = 50000;

    @Value("${custom.llm.api-key}")
    private String apiKey;

    @Value("${custom.llm.url}")
    private String baseUrl;

    @Value("${custom.llm.model}")
    private String model;

    @Resource
    private HybridRetriever hybridRetriever;

    private final RestClient restClient = RestClient.builder().build();

    /** A/B 测试：可开关各模块 */
    @GetMapping("/rag/abtest")
    public Map<String, Object> abtest(
            String question,
            @RequestParam(defaultValue = "true") boolean rewrite,
            @RequestParam(defaultValue = "true") boolean fts,
            @RequestParam(defaultValue = "true") boolean vector,
            @RequestParam(defaultValue = "true") boolean rerank) {

        if (question == null || question.isBlank()) {
            return Map.of("question", "", "contexts", List.of(), "config", Map.of());
        }
        List<Document> docs = hybridRetriever.retrieve(question, 5, rewrite, fts, vector, rerank);
        List<String> contexts = docs.stream().map(Document::getText).toList();

        Map<String, Object> result = new HashMap<>();
        result.put("question", question);
        result.put("contexts", contexts);
        result.put("config", Map.of("rewrite", rewrite, "fts", fts, "vector", vector, "rerank", rerank));
        return result;
    }

    @GetMapping("/rag/retrieve")
    public Map<String, Object> retrieve(String question) {
        if (question == null || question.isBlank()) {
            return Map.of("question", "", "contexts", List.of());
        }
        List<Document> docs = hybridRetriever.retrieve(question, 5);
        List<String> contexts = docs.stream().map(Document::getText).toList();

        List<String> trimmed = new ArrayList<>();
        int total = 0;
        for (String c : contexts) {
            total += c.length();
            if (total > MAX_CONTEXT_CHARS) break;
            trimmed.add(c);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("question", question);
        result.put("contexts", trimmed);
        return result;
    }

    @GetMapping("/rag/chat")
    public Map<String, Object> ragChat(String question) {
        if (question == null || question.isBlank()) {
            return Map.of("question", "", "answer", "请输入问题", "contexts", List.of());
        }

        
        List<Document> docs = hybridRetriever.retrieve(question, 5);

        List<String> contexts = new ArrayList<>();
        for (Document doc : docs) {
            String text = doc.getText();
            int projectedTotal = contexts.stream().mapToInt(String::length).sum() + text.length();
            if (projectedTotal > MAX_CONTEXT_CHARS) break;
            contexts.add(text);
        }

        String systemPrompt = """
                你是ragger，一个面试辅导助手。根据提供的参考资料回答面试问题。

                回答要求：
                1. 如果参考资料中包含相关信息，请基于资料给出清晰准确的回答
                2. 如果参考资料不包含问题相关信息，请说不知道，不要自己编造答案
                3. 回答应结构清晰，重点突出，适合面试场景
                4. 使用中文回答
                """;

        String answer = callLlm(systemPrompt,
                "参考资料：\n" + String.join("\n---\n", contexts) + "\n\n面试问题：" + question);

        Map<String, Object> result = new HashMap<>();
        result.put("question", question);
        result.put("answer", answer);
        result.put("contexts", contexts);
        return result;
    }

    private String callLlm(String system, String user) {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", model);
        requestBody.put("messages", List.of(
                Map.of("role", "system", "content", system),
                Map.of("role", "user", "content", user)
        ));
        requestBody.put("temperature", 0);

        try {
            var response = restClient.post()
                    .uri(baseUrl + "/chat/completions")
                    .header("Authorization", "Bearer " + apiKey)
                    .header("Content-Type", "application/json")
                    .body(requestBody)
                    .retrieve()
                    .toEntity(Map.class);

            Map<String, Object> body = response.getBody();
            if (body != null && body.containsKey("choices")) {
                List<Map<String, Object>> choices = (List<Map<String, Object>>) body.get("choices");
                if (!choices.isEmpty()) {
                    Map<String, Object> message = (Map<String, Object>) choices.get(0).get("message");
                    return (String) message.get("content");
                }
            }
            return "调用 LLM 返回异常";
        } catch (Exception e) {
            return "调用 LLM 失败: " + e.getMessage();
        }
    }
}
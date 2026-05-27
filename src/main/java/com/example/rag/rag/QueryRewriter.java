package com.example.rag.rag;

import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.util.StringUtils;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Component;

import java.util.regex.Pattern;

@Slf4j
@Component
public class QueryRewriter {

    private static final Pattern CODE_FENCE = Pattern.compile("(?s)```.*?```", Pattern.MULTILINE);

    private static final String SYSTEM_PROMPT = """
            你是一个检索(Query)改写器，目标是提升 RAG 的召回效果。

            规则：
            1) 输出只包含【一行】改写后的检索查询，不要解释，不要加前缀
            2) 保留原问题中的关键实体词、技术名词、缩写、数字、英文关键字
            3) 可以补全同义词/更常见的表达，但不要引入与原问题无关的新主题
            4) 长度尽量控制在 20~80 个中文字符（或同等信息量），避免过长
            """;

    @Resource
    private ChatModel dashscopeChatModel;

    private volatile ChatClient chatClient;

    /**
     * 查询改写：失败则回退原问题
     */
    public String rewrite(String question) {
        if (!StringUtils.hasText(question)) {
            return question;
        }

        String original = question.trim();
        if (original.isEmpty()) {
            return question;
        }

        // 避免极端超长输入导致改写成本过高
        String input = original.length() > 512 ? original.substring(0, 512) : original;

        try {
            ChatClient client = getChatClient();
            String raw = client.prompt()
                    .system(SYSTEM_PROMPT)
                    .user("原始问题：" + input + "\n\n改写后的检索查询：")
                    .call()
                    .content();

            String rewritten = normalizeRewrite(raw);
            if (!StringUtils.hasText(rewritten)) {
                return question;
            }

            // 再次限制长度，避免产生超长 query
            if (rewritten.length() > 256) {
                rewritten = rewritten.substring(0, 256);
            }

            if (!rewritten.equals(original)) {
                log.debug("query rewrite: '{}' -> '{}'", original, rewritten);
            }
            return rewritten;
        } catch (Exception e) {
            log.debug("query rewrite failed: {}", e.getMessage());
            return question;
        }
    }

    private ChatClient getChatClient() {
        ChatClient local = this.chatClient;
        if (local != null) {
            return local;
        }
        synchronized (this) {
            if (this.chatClient == null) {
                this.chatClient = ChatClient.builder(dashscopeChatModel).build();
            }
            return this.chatClient;
        }
    }

    private String normalizeRewrite(String raw) {
        if (!StringUtils.hasText(raw)) {
            return "";
        }

        String s = raw.trim();

        // 去掉可能的 code fence
        s = CODE_FENCE.matcher(s).replaceAll("").trim();

        // 只取第一行（避免模型输出多行解释）
        int newline = s.indexOf('\n');
        if (newline > 0) {
            s = s.substring(0, newline).trim();
        }

        // 去掉常见前缀
        for (String prefix : new String[]{"改写：", "改写:", "检索查询：", "检索查询:", "Query:", "query:"}) {
            if (s.startsWith(prefix)) {
                s = s.substring(prefix.length()).trim();
                break;
            }
        }

        // 去掉包裹引号
        if ((s.startsWith("\"") && s.endsWith("\"")) || (s.startsWith("'") && s.endsWith("'"))) {
            s = s.substring(1, s.length() - 1).trim();
        }

        return s;
    }
}
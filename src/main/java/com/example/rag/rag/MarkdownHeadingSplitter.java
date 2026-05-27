package com.example.rag.rag;

import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 按 H4（####）切分文档，保留 H2/H3 层级为 metadata
 *
 * 输入：已按 --- 切分好的 H2 级文档（内容包含标题标记行）
 * 输出：
 *   - 每个 #### 及其内容 → 独立 chunk，metadata 含 h2/h3/h4/question
 *   - 无 #### 的段落 → 原样保留
 */
@Slf4j
@Component
public class MarkdownHeadingSplitter {

    private static final Pattern H4_SPLIT = Pattern.compile("(?m)^####\\s+");

    public List<Document> split(List<Document> documents) {
        List<Document> result = new ArrayList<>();
        for (Document doc : documents) {
            String text = doc.getText();
            if (text == null || text.isBlank()) continue;

            String h2 = (String) doc.getMetadata().get("h2");
            if (h2 == null) h2 = "";

            // 按 #### 切分
            String[] parts = H4_SPLIT.split(text);
            if (parts.length <= 1) {
                // 没有 ####，原样保留
                doc.getMetadata().putIfAbsent("h2", h2);
                result.add(doc);
                continue;
            }

            // 第一个部分是 #### 之前的内容（引言/上下文）
            String beforeFirst = parts[0].trim();
            String currentH3 = "";
            if (!beforeFirst.isEmpty() && beforeFirst.length() > 30) {
                // 把引言作为独立段保留
                Document intro = new Document(beforeFirst);
                intro.getMetadata().putAll(doc.getMetadata());
                intro.getMetadata().put("h2", h2);
                result.add(intro);
            }

            // 处理每个 #### 块
            for (int i = 1; i < parts.length; i++) {
                String part = parts[i].trim();
                if (part.isEmpty()) continue;

                // 第一行是 H4 标题
                int endOfFirstLine = part.indexOf('\n');
                String h4Text = (endOfFirstLine > 0) ? part.substring(0, endOfFirstLine).trim() : part;
                String content = (endOfFirstLine > 0) ? part.substring(endOfFirstLine).trim() : "";

                // 在当前块中查找最近的 ###
                String h3InBlock = findH3Before(parts, i);
                if (!h3InBlock.isEmpty()) currentH3 = h3InBlock;

                String fullContent = "#### " + h4Text + "\n" + content;

                Document newDoc = new Document(fullContent);
                newDoc.getMetadata().putAll(doc.getMetadata());
                newDoc.getMetadata().put("h2", h2);
                newDoc.getMetadata().put("h3", currentH3);
                newDoc.getMetadata().put("h4", h4Text);
                newDoc.getMetadata().put("question", h4Text);
                result.add(newDoc);
            }
        }
        return result;
    }

    /**
     * 在 #### 块之前查找最近的 ### 标题
     */
    private String findH3Before(String[] parts, int currentIndex) {
        // 从 currentIndex 开始往前搜索 ###
        Pattern h3Pat = Pattern.compile("^###\\s+(.+)$", Pattern.MULTILINE);
        for (int i = currentIndex - 1; i >= 0; i--) {
            Matcher m = h3Pat.matcher(parts[i]);
            if (m.find()) {
                return m.group(1).trim();
            }
        }
        return "";
    }
}
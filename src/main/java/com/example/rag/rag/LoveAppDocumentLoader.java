package com.example.rag.rag;

import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.core.io.Resource;
import org.springframework.core.io.support.ResourcePatternResolver;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
@Slf4j
public class LoveAppDocumentLoader {

    private static final Pattern H2_PATTERN = Pattern.compile("^##\\s+(.+)$", Pattern.MULTILINE);
    private static final Pattern H3_PATTERN = Pattern.compile("^###\\s+(.+)$", Pattern.MULTILINE);
    private static final Pattern H4_PATTERN = Pattern.compile("^####\\s+(.+)$", Pattern.MULTILINE);

    private final ResourcePatternResolver resourcePatternResolver;

    public LoveAppDocumentLoader(ResourcePatternResolver resourcePatternResolver) {
        this.resourcePatternResolver = resourcePatternResolver;
    }

    public List<Document> loadMarkdowns() {
        return loadMarkdowns("**");
    }

    public List<Document> loadMarkdowns(String subdirPattern) {
        List<Document> allDocuments = new ArrayList<>();
        try {
            Resource[] resources = resourcePatternResolver.getResources(
                    "classpath:document/" + subdirPattern + "/*.md");
            for (Resource resource : resources) {
                String fileName = resource.getFilename();
                String text;
                try (var in = resource.getInputStream()) {
                    text = new String(in.readAllBytes(), StandardCharsets.UTF_8);
                }
                text = text.replace("\r\n", "\n");
                String[] sections = text.split("\n---\n");
                String currentH2 = "", currentH3 = "";

                for (String section : sections) {
                    if (section == null) continue;
                    section = removeBlankLines(section);
                    if (section.isEmpty()) continue;

                    if (section.startsWith("# ") && section.contains("\n")) {
                        section = section.substring(section.indexOf("\n")).trim();
                    }
                    if (section.isEmpty()) continue;

                    String h2 = extractFirstHeading(section, H2_PATTERN);
                    String h3 = extractFirstHeading(section, H3_PATTERN);
                    String h4 = extractFirstHeading(section, H4_PATTERN);

                    if (h2 != null) {
                        currentH2 = h2;
                        currentH3 = "";
                    }
                    if (h3 != null) currentH3 = h3;

                    Document doc = new Document(section);
                    doc.getMetadata().put("filename", fileName);
                    doc.getMetadata().put("h2", currentH2);

                    if (h3 != null) {
                        doc.getMetadata().put("h3", h3);
                        if (h4 == null) doc.getMetadata().put("question", h3);
                    }
                    if (h4 != null) {
                        doc.getMetadata().put("h4", h4);
                        doc.getMetadata().put("question", h4);
                        if (!currentH3.isEmpty()) {
                            doc.getMetadata().put("h3", currentH3);
                        }
                    }
                    if (h3 == null && h4 == null && h2 != null) {
                        doc.getMetadata().put("question", h2);
                    }

                    allDocuments.add(doc);
                }
            }
        } catch (IOException e) {
            log.error("文档加载失败", e);
        }
        log.info("文档加载完成: {} 篇", allDocuments.size());
        return allDocuments;
    }

    private String removeBlankLines(String text) {
        String[] lines = text.split("\n");
        StringBuilder sb = new StringBuilder();
        for (String line : lines) {
            if (!line.trim().isEmpty()) {
                if (sb.length() > 0) sb.append("\n");
                sb.append(line);
            }
        }
        return sb.toString();
    }

    private String extractFirstHeading(String text, Pattern pattern) {
        Matcher m = pattern.matcher(text);
        if (m.find()) return m.group(1).trim();
        return null;
    }
}
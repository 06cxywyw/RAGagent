package com.example.rag.controller;

import com.example.rag.rag.IngestionService;
import jakarta.annotation.Resource;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@RestController
@RequestMapping("/ops")
public class UploadController {

    @Resource
    private IngestionService ingestionService;

    @PostMapping("/upload")
    public String uploadFile(@RequestParam("file") MultipartFile file) {
        if (file.isEmpty()) return "文件为空";
        try {
            String name = file.getOriginalFilename();
            if (name == null) name = "upload.md";
            Path dir = Paths.get("src/main/resources/document/upload");
            Files.createDirectories(dir);
            Files.write(dir.resolve(name), file.getBytes());
            return "文件已保存并入库:\n" + ingestionService.ingest("upload");
        } catch (Exception e) {
            return "上传失败: " + e.getMessage();
        }
    }
}
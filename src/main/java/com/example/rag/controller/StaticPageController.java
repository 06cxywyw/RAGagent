package com.example.rag.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * 让静态页面支持无文件名访问：
 * - /admin  -> /admin/index.html
 * - /rag    -> /rag/index.html
 */
@Controller
public class StaticPageController {

    @GetMapping({"/admin", "/admin/"})
    public String admin() {
        return "forward:/admin/index.html";
    }

    @GetMapping({"/rag", "/rag/"})
    public String rag() {
        return "forward:/rag/index.html";
    }
}

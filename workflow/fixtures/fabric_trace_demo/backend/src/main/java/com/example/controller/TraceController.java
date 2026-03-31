package com.example.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/trace")
public class TraceController {

    @PostMapping("/batch")
    public String createBatch() {
        return "ok";
    }

    @PostMapping("/transfer")
    public String transferBatch() {
        return "ok";
    }

    @GetMapping("/batch/{id}")
    public String queryBatch() {
        return "ok";
    }
}

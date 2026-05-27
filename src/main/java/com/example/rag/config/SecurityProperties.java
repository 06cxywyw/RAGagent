package com.example.rag.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "security")
public class SecurityProperties {

    private ApiKeys apiKeys = new ApiKeys();

    @Data
    public static class ApiKeys {
        private String dashscopeKey;
        private String searchApiKey;

        public String getDashscopeKey() {
            return dashscopeKey != null ? dashscopeKey :
                   System.getenv("DASHSCOPE_API_KEY");
        }

        public String getSearchApiKey() {
            return searchApiKey != null ? searchApiKey :
                   System.getenv("SEARCH_API_KEY");
        }
    }
}
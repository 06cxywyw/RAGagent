FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY target/rag-standalone-*.jar app.jar
EXPOSE 8123
ENTRYPOINT ["java", "-jar", "app.jar", "--spring.profiles.active=prod"]
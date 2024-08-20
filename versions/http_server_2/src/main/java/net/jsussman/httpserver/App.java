package net.jsussman.httpserver;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

public class App {
  private static final int PORT = 8080;
  private static final Map<String, String> dataStore = new HashMap<>();

  public static void main(String[] args) throws IOException {
    HttpServer server = HttpServer.create(new InetSocketAddress(PORT), 0);
    System.out.println("Server started on port " + PORT);

    server.createContext("/", new RootHandler());
    server.createContext("/data", new DataHandler());

    server.setExecutor(null); // creates a default executor
    server.start();
  }

  static class RootHandler implements HttpHandler {
    @Override
    public void handle(HttpExchange exchange) throws IOException {
      String response = "Welcome to the HTTP Server!";
      exchange.sendResponseHeaders(200, response.length());
      try (OutputStream os = exchange.getResponseBody()) {
        os.write(response.getBytes(StandardCharsets.UTF_8));
      }
    }
  }

  static class DataHandler implements HttpHandler {
    @Override
    public void handle(HttpExchange exchange) throws IOException {
      String method = exchange.getRequestMethod();
      String path = exchange.getRequestURI().getPath();

      if ("GET".equalsIgnoreCase(method)) {
        handleGetRequest(exchange, path);
      } else if ("POST".equalsIgnoreCase(method)) {
        handlePostRequest(exchange, path);
      } else {
        handleNotFound(exchange);
      }
    }

    private void handleGetRequest(HttpExchange exchange, String path) throws IOException {
      String key = path.substring("/data/".length());
      String response = dataStore.getOrDefault(key, "Not Found");
      exchange.sendResponseHeaders(200, response.length());
      try (OutputStream os = exchange.getResponseBody()) {
        os.write(response.getBytes(StandardCharsets.UTF_8));
      }
    }

    private void handlePostRequest(HttpExchange exchange, String path) throws IOException {
      String key = path.substring("/data/".length());
      InputStream inputStream = exchange.getRequestBody();
      String body = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
      dataStore.put(key, body);
      String response = "Data stored successfully!";
      exchange.sendResponseHeaders(200, response.length());
      try (OutputStream os = exchange.getResponseBody()) {
        os.write(response.getBytes(StandardCharsets.UTF_8));
      }
    }

    private void handleNotFound(HttpExchange exchange) throws IOException {
      String response = "404 - Not Found";
      exchange.sendResponseHeaders(404, response.length());
      try (OutputStream os = exchange.getResponseBody()) {
        os.write(response.getBytes(StandardCharsets.UTF_8));
      }
    }
  }
}

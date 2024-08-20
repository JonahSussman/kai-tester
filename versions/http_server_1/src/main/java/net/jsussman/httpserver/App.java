package net.jsussman.httpserver;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.HashMap;
import java.util.Map;

public class App {
  private static final int PORT = 8080;
  private static final Map<String, String> dataStore = new HashMap<>();

  public static void main(String[] args) throws IOException {
    ServerSocket serverSocket = new ServerSocket(PORT);
    System.out.println("Server started on port " + PORT);

    while (true) {
      try (Socket clientSocket = serverSocket.accept()) {
        BufferedReader in =
            new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
        OutputStream out = clientSocket.getOutputStream();

        // Read the request line (e.g., "GET / HTTP/1.1")
        String requestLine = in.readLine();
        if (requestLine == null || requestLine.isEmpty()) {
          continue;
        }

        String[] tokens = requestLine.split(" ");
        String method = tokens[0];
        String path = tokens[1];

        if (method.equals("GET")) {
          handleGetRequest(out, path);
        } else if (method.equals("POST")) {
          handlePostRequest(in, out, path);
        } else {
          handleNotFound(out);
        }

        out.flush();
      } catch (IOException e) {
        e.printStackTrace();
      }
    }
  }

  private static void handleGetRequest(OutputStream out, String path) throws IOException {
    if ("/".equals(path)) {
      String response =
          "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nWelcome to the HTTP Server!";
      out.write(response.getBytes());
    } else if (path.startsWith("/data")) {
      String key = path.substring("/data/".length());
      String value = dataStore.getOrDefault(key, "Not Found");
      String response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n" + value;
      out.write(response.getBytes());
    } else {
      handleNotFound(out);
    }
  }

  private static void handlePostRequest(BufferedReader in, OutputStream out, String path)
      throws IOException {
    if (path.startsWith("/data")) {
      String key = path.substring("/data/".length());
      StringBuilder body = new StringBuilder();
      String line;
      while (!(line = in.readLine()).isEmpty()) {
        // Read until the empty line after headers
      }
      while (in.ready() && (line = in.readLine()) != null) {
        body.append(line);
      }
      dataStore.put(key, body.toString());
      String response =
          "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nData stored successfully!";
      out.write(response.getBytes());
    } else {
      handleNotFound(out);
    }
  }

  private static void handleNotFound(OutputStream out) throws IOException {
    String response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\n\r\n404 - Not Found";
    out.write(response.getBytes());
  }
}

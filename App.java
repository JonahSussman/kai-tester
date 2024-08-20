package io.konveyor.filer;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class App {

  public static void main(String[] args) {
    Path sourceDir = Paths.get("source_directory");
    Path destDir = Paths.get("destination_directory");
    try {
      copyDirectoryNIO(sourceDir, destDir);
      System.out.println("Directory copied successfully using NIO.");
    } catch (IOException e) {
      e.printStackTrace();
    }
  }

  public static void copyDirectoryNIO(Path source, Path destination) throws IOException {
    if (Files.isDirectory(source)) {
      if (!Files.exists(destination)) {
        Files.createDirectory(destination); // Create destination directory if it doesn't exist
      }
      Files.walk(source)
          .filter(path -> !Files.isDirectory(path))
          .forEach(
              path -> {
                Path relativePath = source.relativize(path);
                Path targetPath = destination.resolve(relativePath);
                try {
                  Files.copy(path, targetPath);
                } catch (IOException e) {
                  e.printStackTrace();
                }
              });
    } else {
      copyFileNIO(source, destination);
    }
  }

  private static void copyFileNIO(Path source, Path destination) throws IOException {
    try (InputStream in = new FileInputStream(source.toFile());
        OutputStream out = new FileOutputStream(destination.toFile())) {

      byte[] buffer = new byte[1024];
      int bytesRead;
      while ((bytesRead = in.read(buffer)) != -1) {
        out.write(buffer, 0, bytesRead);
      }
    }
  }
}

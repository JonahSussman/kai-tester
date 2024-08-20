package io.konveyor.filer;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;

public class App {
  public static void main(String[] args) {
    File sourceDir = new File("source_directory");
    File destDir = new File("destination_directory");

    try {
      copyDirectoryLegacyIO(sourceDir, destDir);
      System.out.println("Directory copied successfully using legacy I/O.");
    } catch (IOException e) {
      e.printStackTrace();
    }
  }

  public static void copyDirectoryLegacyIO(File source, File destination) throws IOException {
    if (source.isDirectory()) {
      if (!destination.exists()) {
        destination.mkdirs(); // Create destination directory if it doesn't exist
      }
      String[] children = source.list();
      if (children != null) {
        for (String child : children) {
          copyDirectoryLegacyIO(new File(source, child), new File(destination, child));
        }
      }
    } else {
      copyFileLegacyIO(source, destination);
    }
  }

  private static void copyFileLegacyIO(File source, File destination) throws IOException {
    try (FileInputStream in = new FileInputStream(source);
        FileOutputStream out = new FileOutputStream(destination)) {

      byte[] buffer = new byte[1024];
      int bytesRead;
      while ((bytesRead = in.read(buffer)) != -1) {
        out.write(buffer, 0, bytesRead);
      }
    }
  }
}

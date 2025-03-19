import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.JSONObject;

public class HprofAnalyzer {

    public static void main(String[] args) {
        if (args.length != 1) {
            System.out.println("Usage: java HprofAnalyzer <path_to_hprof_file>");
            return;
        }

        String hprofFilePath = args[0];
        try {
            // Parse the .hprof file and extract necessary data
            JSONObject analysisResult = parseHprofFile(hprofFilePath);

            // Send the JSON data to the FastAPI server
            sendJsonToFastAPI(analysisResult);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static JSONObject parseHprofFile(String filePath) throws IOException {
        // Implement your .hprof parsing logic here
        // For demonstration, returning a sample JSON object
        JSONObject json = new JSONObject();
        json.put("heapSummary", "Sample summary of heap analysis");
        json.put("leakSuspects", "Sample leak suspects data");
        return json;
    }

    private static void sendJsonToFastAPI(JSONObject jsonData) throws IOException {
        URL url = new URL("http://127.0.0.1:8000/analyze");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/json; utf-8");
        conn.setDoOutput(true);

        try (OutputStream os = conn.getOutputStream()) {
            byte[] input = jsonData.toString().getBytes("utf-8");
            os.write(input, 0, input.length);
        }

        int responseCode = conn.getResponseCode();
        System.out.println("POST Response Code :: " + responseCode);

        if (responseCode == HttpURLConnection.HTTP_OK) {
            try (BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream(), "utf-8"))) {
                StringBuilder response = new StringBuilder();
                String responseLine;
                while ((responseLine = br.readLine()) != null) {
                    response.append(responseLine.trim());
                }
                System.out.println("Response from FastAPI: " + response.toString());
            }
        } else {
            System.out.println("POST request not worked");
        }
    }
}
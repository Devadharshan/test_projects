memory-analyzer/
├── java/
│   ├── src/
│   │   └── HprofAnalyzer.java
│   ├── lib/
│   │   ├── jackson-annotations.jar
│   │   ├── jackson-core.jar
│   │   ├── jackson-databind.jar
│   │   └── org.eclipse.mat.core.jar
│   ├── target/
│   │   └── hprof-analyzer.jar
│   └── compile_and_package.sh
├── python/
│   ├── main.py
│   ├── config.json
│   └── requirements.txt
└── README.import com.fasterxml.jackson.databind.ObjectMapper;
import org.eclipse.mat.snapshot.ISnapshot;
import org.eclipse.mat.snapshot.SnapshotFactory;
import org.eclipse.mat.snapshot.model.IThreadStack;
import org.eclipse.mat.snapshot.model.IThreadStackFrame;
import org.eclipse.mat.util.VoidProgressListener;

import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

public class HprofAnalyzer {

    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java -jar hprof-analyzer.jar <hprof-file>");
            return;
        }

        String hprofFilePath = args[0];
        File hprofFile = new File(hprofFilePath);

        try {
            // Load the .hprof file
            ISnapshot snapshot = SnapshotFactory.openSnapshot(hprofFile, new HashMap<>(), new VoidProgressListener());

            // Analyze threads and memory usage
            List<ThreadInfo> analysisResult = new ArrayList<>();
            for (IThreadStack thread : snapshot.getThreads()) {
                ThreadInfo threadInfo = new ThreadInfo();
                threadInfo.setThreadName(thread.getThreadName());
                threadInfo.setMemoryUsage(snapshot.getHeapSize(thread.getThreadId()));

                // Add stack trace
                StringBuilder stackTrace = new StringBuilder();
                for (IThreadStackFrame frame : thread.getStackFrames()) {
                    stackTrace.append(frame.getText()).append("\n");
                }
                threadInfo.setStackTrace(stackTrace.toString());

                analysisResult.add(threadInfo);
            }

            // Serialize analysis results to JSON
            ObjectMapper mapper = new ObjectMapper();
            String json = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(analysisResult);

            // Output JSON
            System.out.println(json);

            // Clean up
            snapshot.dispose();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}

class ThreadInfo {
    private String threadName;
    private long memoryUsage;
    private String stackTrace;

    // Getters and setters
    public String getThreadName() {
        return threadName;
    }

    public void setThreadName(String threadName) {
        this.threadName = threadName;
    }

    public long getMemoryUsage() {
        return memoryUsage;
    }

    public void setMemoryUsage(long memoryUsage) {
        this.memoryUsage = memoryUsage;
    }

    public String getStackTrace() {
        return stackTrace;
    }

    public void setStackTrace(String stackTrace) {
        this.stackTrace = stackTrace;
    }
}





------------////---





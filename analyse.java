package com.example.analyzer;

import org.eclipse.mat.snapshot.ISnapshot;
import org.eclipse.mat.snapshot.SnapshotFactory;
import org.eclipse.mat.snapshot.model.IClass;
import org.eclipse.mat.util.VoidProgressListener;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.File;
import java.io.FileWriter;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

public class HprofAnalyzer {
    public static void main(String[] args) {
        if (args.length != 2) {
            System.out.println("Usage: java HprofAnalyzer <hprof_file_path> <output_json_path>");
            return;
        }

        String hprofFilePath = args[0];
        String outputJsonPath = args[1];

        try {
            ISnapshot snapshot = SnapshotFactory.openSnapshot(new File(hprofFilePath), new VoidProgressListener());
            Collection<IClass> classes = snapshot.getClasses();

            Map<String, Object> analysisResult = new HashMap<>();
            for (IClass clazz : classes) {
                Map<String, Object> classInfo = new HashMap<>();
                classInfo.put("instanceCount", clazz.getNumberOfObjects());
                classInfo.put("shallowHeapSize", clazz.getHeapSizePerInstance());

                analysisResult.put(clazz.getName(), classInfo);
            }

            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            try (FileWriter writer = new FileWriter(outputJsonPath)) {
                gson.toJson(analysisResult, writer);
            }

            System.out.println("Analysis complete. Results saved to: " + outputJsonPath);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}






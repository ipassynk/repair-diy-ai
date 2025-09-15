import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";
import { useCompletion } from "@ai-sdk/react";

interface RepairQA {
  question: string;
  answer: string;
  equipment_problem: string;
  tools_required: string[];
  steps: string[];
  safety_info: string;
  tips: string;
}

function App() {
  const [category, setCategory] = useState("random");
  const [parsedData, setParsedData] = useState<RepairQA[]>([]);
  const [showRawJson, setShowRawJson] = useState(false);

  const { completion, complete, isLoading, error } = useCompletion({
    api: "/api/generate",
    body: {
      category,
    },
    streamProtocol: "text",
    onFinish: (prompt: string, completion: string) => {
      console.log("Finished streaming completion:", completion);
      // Try to parse JSON from completion
      try {
        const jsonMatch = completion.match(/\[[\s\S]*\]/);
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0]);
          setParsedData(parsed);
          setShowRawJson(false);
        }
      } catch (e) {
        console.log("Could not parse JSON from completion");
      }
    },
    onError: (error: Error) => {
      console.error("An error occurred:", error);
    },
  });

  const handleGenerate = () => {
    console.log("Starting generation for category:", category);
    setParsedData([]);
    setShowRawJson(true); // Clear previous data
    complete("");
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8">Repair DIY AI</h1>
        <div className="text-center text-muted-foreground mb-8">
          <p>
            Mini Project 1: Synthetic Data on Home DIY / Repair QA for AI
            Engineer Bootcamp. Use The AI Toolkit for TypeScript, FastAPI, OpenAI, LLM as Judge.
          </p>
        </div>

        <div className="max-w-4xl mx-auto mb-8">
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">
                Select Repair Category
              </label>
              <Select onValueChange={setCategory} value={category}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Choose a repair category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="appliance">Appliance Repair</SelectItem>
                  <SelectItem value="plumbing">Plumbing</SelectItem>
                  <SelectItem value="electrical">Electrical</SelectItem>
                  <SelectItem value="hvac">HVAC</SelectItem>
                  <SelectItem value="general">General</SelectItem>
                  <SelectItem value="random">Random</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleGenerate} disabled={isLoading}>
              {isLoading ? "Generating..." : "Generate QA Pairs"}
            </Button>
          </div>
        </div>

        {/* Debug info */}
        <div className="max-w-4xl mx-auto mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded flex justify-between items-center">
          <div>
            <p>Completion length: {completion?.length || 0}</p>
            <p>Is loading: {isLoading ? "Yes" : "No"}</p>
            <p>Parsed data count: {parsedData.length}</p>
          </div>

          <Button
            className="align-center"
            variant="outline"
            size="sm"
            onClick={() => setShowRawJson(!showRawJson)}
          >
            {showRawJson ? "Hide" : "Show"} Raw JSON
          </Button>
        </div>

        {showRawJson && (
          <div className="max-w-4xl mx-auto mb-6">
            <pre className="whitespace-pre-wrap text-sm leading-relaxed overflow-auto max-h-96 bg-white p-4 rounded border">
              {completion ||
                "No content yet. Click Generate QA Pairs to start."}
            </pre>
          </div>
        )}

        {error && (
          <div className="max-w-4xl mx-auto mt-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">Error: {error.message}</p>
            </div>
          </div>
        )}

        {parsedData.length > 0 && (
          <div className="max-w-6xl mx-auto mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Generated Repair Q&A</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {parsedData.map((item, index) => (
                <div
                  key={index}
                  className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden"
                >
                  {/* Question Header */}
                  <div className="bg-blue-50 border-b border-blue-200 p-3">
                    <h3 className="text-sm font-semibold text-blue-800 line-clamp-2">
                      {item.question}
                    </h3>
                  </div>

                  <div className="p-4 space-y-3">
                    <div className="flex gap-2">
                      <h4 className="font-medium text-red-700 text-xs mb-1">
                        Safety:
                      </h4>
                      <p className="text-red-700 rounded text-xs">
                        {item.safety_info}
                      </p>
                    </div>

                    <div className="flex gap-2">
                      <h4 className="font-medium text-gray-800 text-xs mb-1">
                        Answer:
                      </h4>
                      <p className="text-gray-600 rounded text-xs">
                        {item.answer}
                      </p>
                    </div>

                    {/* Equipment Problem */}
                    <div className="flex gap-2">
                      <h4 className="font-medium text-gray-800 text-xs mb-1">
                        Equipment Problem:
                      </h4>
                      <p className="text-gray-600 rounded text-xs">
                        {item.equipment_problem}
                      </p>
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-800 text-xs mb-1">
                        Tools Required:
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {item.tools_required.map((tool, toolIndex) => (
                          <span
                            key={toolIndex}
                            className="inline-flex items-center px-1 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200"
                          >
                            {tool}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-800 text-xs mb-1">
                        Steps:
                      </h4>
                      <ol className="list-decimal list-inside space-y-1 text-gray-600 bg-gray-50 p-2 rounded text-xs">
                        {item.steps.map((step, stepIndex) => (
                          <li key={stepIndex} className="leading-relaxed">
                            {step}
                          </li>
                        ))}
                      </ol>
                    </div>

                    <div className="bg-blue-50 border-l-4 border-blue-400 p-2 rounded-r">
                      <div className="flex items-start">
                        <div>
                          <h4 className="font-medium text-blue-800 text-xs mb-1">
                            Tips
                          </h4>
                          <p className="text-blue-700 italic text-xs">
                            {item.tips}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

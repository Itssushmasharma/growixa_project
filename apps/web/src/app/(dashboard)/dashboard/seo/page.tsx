"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api-client";
import { SearchIcon, AlertTriangleIcon, CheckCircle2Icon, InfoIcon } from "lucide-react";

interface SEOAnalysisResult {
  url: string;
  score: number;
  title: string | null;
  description: string | null;
  h1_count: number;
  image_count: number;
  images_missing_alt: number;
  is_https: boolean;
  warnings: string[];
  recommendations: string[];
  error?: string;
}

export default function SEOAnalysisPage() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SEOAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const data = await apiFetch<SEOAnalysisResult>("/seo/analyze", {
        method: "POST",
        body: JSON.stringify({ url })
      });
      if (data.error) {
        setError(data.error);
      }
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to analyze website.");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-emerald-500";
    if (score >= 70) return "text-amber-500";
    return "text-red-500";
  };

  return (
    <div className="max-w-5xl mx-auto p-6 md:p-8 space-y-8">
      <div className="flex flex-col items-center justify-center text-center space-y-4 mb-8">
        <h1 className="text-3xl font-bold text-slate-900">SEO Website Audit</h1>
        <p className="text-slate-500 max-w-lg text-lg">
          Instantly check your website's search engine health. Find critical issues and optimize your content for better rankings.
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-2 max-w-2xl mx-auto">
        <form onSubmit={handleAnalyze} className="flex gap-2">
          <input 
            type="url"
            required
            placeholder="Enter website URL (e.g., https://example.com)"
            className="flex-1 rounded-lg border-0 bg-transparent px-4 focus:ring-0 sm:text-base text-slate-900 placeholder:text-slate-400"
            value={url}
            onChange={e => setUrl(e.target.value)}
            disabled={loading}
          />
          <button 
            type="submit"
            disabled={loading || !url}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-medium shadow-sm flex items-center gap-2 disabled:opacity-50 transition-colors"
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <SearchIcon className="w-5 h-5" />
            )}
            Analyze
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-center font-medium max-w-2xl mx-auto">
          {error}
        </div>
      )}

      {result && !result.error && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          {/* Main Score Card */}
          <div className="md:col-span-1">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 text-center h-full flex flex-col justify-center items-center">
              <span className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Overall Score</span>
              <div className={`text-7xl font-black ${getScoreColor(result.score)} tracking-tighter`}>
                {result.score}
              </div>
              <span className="text-slate-500 mt-4 font-medium">Out of 100</span>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="md:col-span-2 grid grid-cols-2 gap-4">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Title Tag</span>
              {result.title ? (
                <div>
                  <p className="text-sm font-medium text-slate-900 truncate" title={result.title}>{result.title}</p>
                  <p className="text-xs text-slate-500 mt-1">{result.title.length} characters</p>
                </div>
              ) : (
                <p className="text-sm text-red-500 font-medium flex items-center gap-1"><AlertTriangleIcon className="w-4 h-4"/> Missing</p>
              )}
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Security</span>
              <p className={`text-sm font-medium flex items-center gap-1 ${result.is_https ? "text-emerald-600" : "text-red-500"}`}>
                {result.is_https ? <><CheckCircle2Icon className="w-4 h-4"/> HTTPS Enabled</> : <><AlertTriangleIcon className="w-4 h-4"/> Not Secure</>}
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">H1 Headings</span>
              <p className={`text-sm font-medium ${result.h1_count === 1 ? "text-emerald-600" : "text-amber-500"}`}>
                {result.h1_count} tag(s) found
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Image Alt Text</span>
              <p className={`text-sm font-medium ${result.images_missing_alt === 0 ? "text-emerald-600" : "text-red-500"}`}>
                {result.images_missing_alt} / {result.image_count} missing alt
              </p>
            </div>
          </div>

          {/* Warnings & Recommendations */}
          <div className="md:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
            <div className="bg-amber-50/50 rounded-2xl border border-amber-100 p-6">
              <h3 className="text-lg font-bold text-amber-900 flex items-center gap-2 mb-4">
                <AlertTriangleIcon className="w-5 h-5 text-amber-500" />
                Issues Found ({result.warnings.length})
              </h3>
              {result.warnings.length === 0 ? (
                <p className="text-sm text-amber-700/70">No major issues found. Great job!</p>
              ) : (
                <ul className="space-y-3">
                  {result.warnings.map((w, i) => (
                    <li key={i} className="text-sm text-amber-800 flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0 mt-1.5" />
                      {w}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="bg-emerald-50/50 rounded-2xl border border-emerald-100 p-6">
              <h3 className="text-lg font-bold text-emerald-900 flex items-center gap-2 mb-4">
                <InfoIcon className="w-5 h-5 text-emerald-500" />
                Recommendations
              </h3>
              {result.recommendations.length === 0 ? (
                <p className="text-sm text-emerald-700/70">Your page is fully optimized.</p>
              ) : (
                <ul className="space-y-3">
                  {result.recommendations.map((r, i) => (
                    <li key={i} className="text-sm text-emerald-800 flex items-start gap-2">
                      <CheckCircle2Icon className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                      {r}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
          
        </div>
      )}
    </div>
  );
}

import os
import glob

def rotate_internal_traces(limit=20):
    trace_dir = r"d:/ГО Талан UA/Talan UA Antigravity manager/.agents/internal_forensics/decision_traces"
    if not os.path.exists(trace_dir):
        print(f"Directory {trace_dir} not found.")
        return

    traces = sorted(glob.glob(os.path.join(trace_dir, "*.md")), key=os.path.getmtime)
    
    if len(traces) > limit:
        to_delete = traces[:-limit]
        for f in to_delete:
            os.remove(f)
            print(f"🧹 Cleaned up old trace: {os.path.basename(f)}")
    else:
        print(f"Memory within limits: {len(traces)}/{limit}")

if __name__ == "__main__":
    rotate_internal_traces()

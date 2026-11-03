using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace ModSwap;

public class Backend : IDisposable
{
	private Process proc;

	private readonly StringBuilder err = new StringBuilder();

	public static string AppDir
	{
		get
		{
			string processPath = Environment.ProcessPath;
			return ((processPath != null) ? System.IO.Path.GetDirectoryName(processPath) : null) ?? AppContext.BaseDirectory;
		}
	}

	private static string FindPython()
	{
		string environmentVariable = Environment.GetEnvironmentVariable("MODSWAP_PY");
		if (!string.IsNullOrEmpty(environmentVariable) && File.Exists(environmentVariable))
		{
			return environmentVariable;
		}
		string text = System.IO.Path.Combine(AppDir, "runtime", "python.exe");
		if (File.Exists(text))
		{
			return text;
		}
		return "python";
	}

	public async Task<string> Start()
	{
		ProcessStartInfo processStartInfo = new ProcessStartInfo
		{
			FileName = FindPython(),
			Arguments = "-u -X utf8 -m modswap serve --port 8765",
			WorkingDirectory = AppDir,
			UseShellExecute = false,
			CreateNoWindow = true,
			RedirectStandardInput = true,
			RedirectStandardOutput = true,
			RedirectStandardError = true,
			StandardOutputEncoding = Encoding.UTF8,
			StandardErrorEncoding = Encoding.UTF8
		};
		processStartInfo.Environment["PYTHONUNBUFFERED"] = "1";
		processStartInfo.Environment["PYTHONUTF8"] = "1";
		processStartInfo.Environment["PYTHONNOUSERSITE"] = "1";
		proc = Process.Start(processStartInfo);
		TaskCompletionSource<string> tcs = new TaskCompletionSource<string>();
		proc.OutputDataReceived += delegate(object s, DataReceivedEventArgs e)
		{
			if (e.Data != null)
			{
				App.Log("py: " + e.Data);
				Match match = Regex.Match(e.Data, "http://127\\.0\\.0\\.1:(\\d+)");
				if (match.Success)
				{
					tcs.TrySetResult("http://127.0.0.1:" + match.Groups[1].Value);
				}
			}
		};
		proc.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e)
		{
			if (e.Data != null)
			{
				lock (err)
				{
					err.AppendLine(e.Data);
				}
				App.Log("py!: " + e.Data);
			}
		};
		proc.EnableRaisingEvents = true;
		proc.Exited += delegate
		{
			tcs.TrySetException(new ApiException("The engine stopped while starting.\n" + Tail()));
		};
		proc.BeginOutputReadLine();
		proc.BeginErrorReadLine();
		if (await Task.WhenAny(tcs.Task, Task.Delay(TimeSpan.FromSeconds(60.0))) != tcs.Task)
		{
			throw new ApiException("The engine did not start in time.\n" + Tail());
		}
		return await tcs.Task;
	}

	private string Tail()
	{
		lock (err)
		{
			string text = err.ToString().Trim();
			return (text.Length > 700) ? text.Substring(text.Length - 700) : text;
		}
	}

	public void Dispose()
	{
		try
		{
			proc?.StandardInput.Close();
		}
		catch
		{
		}
		try
		{
			if (proc != null && !proc.WaitForExit(1200))
			{
				proc.Kill(entireProcessTree: true);
			}
		}
		catch
		{
		}
	}
}

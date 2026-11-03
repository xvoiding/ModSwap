using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace ModSwap;

public class Api
{
	private readonly HttpClient http = new HttpClient
	{
		Timeout = TimeSpan.FromMinutes(30.0)
	};

	public string Base = "";

	private static JsonElement Parse(string text)
	{
		using JsonDocument jsonDocument = JsonDocument.Parse(text);
		return jsonDocument.RootElement.Clone();
	}

	private static async Task<JsonElement> Read(HttpResponseMessage r)
	{
		string text = await r.Content.ReadAsStringAsync();
		JsonElement result;
		try
		{
			result = Parse(text);
		}
		catch
		{
			throw new ApiException("The engine sent something unreadable (" + (int)r.StatusCode + ").");
		}
		if (result.ValueKind == JsonValueKind.Object && result.TryGetProperty("error", out var value) && value.ValueKind == JsonValueKind.String)
		{
			throw new ApiException(value.GetString());
		}
		return result;
	}

	public async Task<JsonElement> Get(string path)
	{
		using HttpResponseMessage r = await http.GetAsync(Base + path);
		return await Read(r);
	}

	public async Task<byte[]> GetBytes(string path)
	{
		using HttpResponseMessage r = await http.GetAsync(Base + path);
		if (!r.IsSuccessStatusCode)
		{
			return null;
		}
		return await r.Content.ReadAsByteArrayAsync();
	}

	public async Task<JsonElement> Post(string path, object body = null)
	{
		string content = JsonSerializer.Serialize(body ?? new Dictionary<string, object>());
		using HttpResponseMessage r = await http.PostAsync(Base + path, new StringContent(content, Encoding.UTF8, "application/json"));
		return await Read(r);
	}

	public async Task<JsonElement> Put(string sid, string file)
	{
		FileInfo fileInfo = new FileInfo(file);
		using FileStream fs = File.OpenRead(file);
		StreamContent streamContent = new StreamContent(fs);
		streamContent.Headers.ContentLength = fileInfo.Length;
		streamContent.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
		string requestUri = Base + "/api/upload?sid=" + Uri.EscapeDataString(sid) + "&name=" + Uri.EscapeDataString(fileInfo.Name);
		using HttpResponseMessage r = await http.PutAsync(requestUri, streamContent);
		return await Read(r);
	}

	public async Task Delete(string path)
	{
		using (await http.DeleteAsync(Base + path))
		{
		}
	}

	public async Task<JsonElement> Job(string id, Action<List<string>> onLog)
	{
		JsonElement jsonElement;
		while (true)
		{
			jsonElement = await Get("/api/job?id=" + id);
			List<string> list = new List<string>();
			if (jsonElement.TryGetProperty("log", out var value) && value.ValueKind == JsonValueKind.Array)
			{
				foreach (JsonElement item in value.EnumerateArray())
				{
					list.Add(item.GetString());
				}
			}
			onLog?.Invoke(list);
			if (jsonElement.GetProperty("done").GetBoolean())
			{
				break;
			}
			await Task.Delay(280);
		}
		if (jsonElement.TryGetProperty("error", out var value2) && value2.ValueKind == JsonValueKind.String)
		{
			throw new ApiException(value2.GetString());
		}
		return jsonElement.GetProperty("result");
	}
}

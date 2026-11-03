using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Windows;
using System.Windows.Media;

namespace ModSwap;

public class MarketRow : INotifyPropertyChanged
{
	private ImageSource preview;

	public string Id { get; set; }

	public string Name { get; set; }

	public string Author { get; set; }

	public string Desc { get; set; }

	public string Category { get; set; }

	public string[] TagList { get; set; } = new string[0];


	public string[] Games { get; set; } = new string[0];


	public long Size { get; set; }

	public bool HasPreview { get; set; }

	public bool ForThisGame { get; set; }

	public ImageSource Preview
	{
		get
		{
			return preview;
		}
		set
		{
			preview = value;
			this.PropertyChanged?.Invoke(this, new PropertyChangedEventArgs("Preview"));
			this.PropertyChanged?.Invoke(this, new PropertyChangedEventArgs("NoPreviewVis"));
		}
	}

	public Visibility NoPreviewVis
	{
		get
		{
			if (preview == null)
			{
				return (Visibility)0;
			}
			return (Visibility)2;
		}
	}

	public string Initial
	{
		get
		{
			if (!string.IsNullOrEmpty(Name))
			{
				return Name.Trim().Substring(0, 1).ToUpperInvariant();
			}
			return "?";
		}
	}

	public string Sub
	{
		get
		{
			List<string> list = new List<string>();
			if (!string.IsNullOrEmpty(Author))
			{
				list.Add("by " + Author);
			}
			if (Size > 0)
			{
				list.Add((Size >= 1048576) ? (((double)Size / 1048576.0).ToString("0.#") + " MB") : (Math.Max(1L, Size / 1024) + " KB"));
			}
			return string.Join("  ·  ", list);
		}
	}

	public string License { get; set; }

	public string Url { get; set; }

	public string TagsText { get; set; }

	public string Tags => TagsText ?? string.Join("  ", TagList.Select((string t) => "#" + t));

	public Visibility TagsVis
	{
		get
		{
			if (string.IsNullOrEmpty(Tags))
			{
				return (Visibility)2;
			}
			return (Visibility)0;
		}
	}

	public Visibility ViewVis
	{
		get
		{
			if (string.IsNullOrEmpty(Url))
			{
				return (Visibility)2;
			}
			return (Visibility)0;
		}
	}

	public bool IsSketchfab
	{
		get
		{
			if (Id != null)
			{
				return Id.StartsWith("sf:");
			}
			return false;
		}
	}

	public event PropertyChangedEventHandler PropertyChanged;
}

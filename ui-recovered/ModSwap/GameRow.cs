using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Media;

namespace ModSwap;

public class GameRow : INotifyPropertyChanged
{
	private ImageSource art;

	public bool ArtTried;

	public ImageSource Art
	{
		get
		{
			return art;
		}
		set
		{
			art = value;
			PropertyChangedEventHandler propertyChanged = this.PropertyChanged;
			if (propertyChanged != null)
			{
				propertyChanged(this, new PropertyChangedEventArgs("Art"));
				propertyChanged(this, new PropertyChangedEventArgs("NoArtVis"));
			}
		}
	}

	public Visibility NoArtVis
	{
		get
		{
			if (art == null)
			{
				return (Visibility)0;
			}
			return (Visibility)2;
		}
	}

	public string Initials
	{
		get
		{
			List<string> list = (from Match m in Regex.Matches(Name ?? "", "[A-Za-z0-9]+")
				select m.Value into x
				where x.Length > 0
				select x).ToList();
			if (list.Count != 0)
			{
				string text;
				if (list.Count != 1)
				{
					char reference = list[0][0];
					ReadOnlySpan<char> readOnlySpan = new ReadOnlySpan<char>(ref reference);
					char reference2 = list[1][0];
					text = string.Concat(readOnlySpan, new ReadOnlySpan<char>(ref reference2));
				}
				else
				{
					text = list[0].Substring(0, Math.Min(2, list[0].Length));
				}
				return text.ToUpperInvariant();
			}
			return "?";
		}
	}

	public Brush Fallback
	{
		get
		{
			//IL_002d: Unknown result type (might be due to invalid IL or missing references)
			//IL_0035: Unknown result type (might be due to invalid IL or missing references)
			//IL_0043: Unknown result type (might be due to invalid IL or missing references)
			//IL_0048: Unknown result type (might be due to invalid IL or missing references)
			//IL_004f: Expected O, but got Unknown
			int num = Math.Abs((Name ?? "").GetHashCode()) % 4;
			byte num2 = (byte)(18 + num * 3);
			byte b = (byte)(30 + num * 4);
			LinearGradientBrush val = new LinearGradientBrush(Color.FromRgb(num2, num2, num2), Color.FromRgb(b, b, b), 55.0);
			((Freezable)val).Freeze();
			return (Brush)val;
		}
	}

	public string AppId { get; set; }

	public string Id { get; set; }

	public string Name { get; set; }

	public string Sub { get; set; }

	public string Root { get; set; }

	public string Label { get; set; }

	public bool Supported { get; set; }

	public string Engine { get; set; }

	public Visibility DotVis
	{
		get
		{
			if (Supported)
			{
				return (Visibility)0;
			}
			return (Visibility)2;
		}
	}

	public event PropertyChangedEventHandler PropertyChanged;
}

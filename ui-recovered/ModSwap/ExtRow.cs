using System.Windows;

namespace ModSwap;

public class ExtRow
{
	public string Id { get; set; }

	public string Name { get; set; }

	public string Sub { get; set; }

	public bool Enabled { get; set; }

	public string ToggleText
	{
		get
		{
			if (!Enabled)
			{
				return "Turn on";
			}
			return "Turn off";
		}
	}

	public Visibility OnVis
	{
		get
		{
			if (Enabled)
			{
				return (Visibility)0;
			}
			return (Visibility)2;
		}
	}
}

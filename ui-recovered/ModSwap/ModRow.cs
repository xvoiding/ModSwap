using System.Windows;

namespace ModSwap;

public class ModRow
{
	public string Id { get; set; }

	public string Name { get; set; }

	public string Sub { get; set; }

	public string Pak { get; set; }

	public bool Active { get; set; }

	public string ActionText
	{
		get
		{
			if (!Active)
			{
				return "Install";
			}
			return "Uninstall";
		}
	}

	public Visibility ActiveVis
	{
		get
		{
			if (Active)
			{
				return (Visibility)0;
			}
			return (Visibility)2;
		}
	}
}

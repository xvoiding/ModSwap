using System.Windows;

namespace ModSwap;

public class CharRow
{
	public int Index { get; set; }

	public string Label { get; set; }

	public string Sub { get; set; }

	public string Cat { get; set; } = "";


	public bool Hidden { get; set; }

	public string Tag
	{
		get
		{
			if (!(Cat == "character"))
			{
				if (!(Cat == "vehicle"))
				{
					if (!(Cat == "weapon"))
					{
						if (!Hidden)
						{
							return "";
						}
						return Cat;
					}
					return "weapon";
				}
				return "vehicle";
			}
			return "person";
		}
	}

	public Visibility TagVis
	{
		get
		{
			if (string.IsNullOrEmpty(Tag))
			{
				return (Visibility)2;
			}
			return (Visibility)0;
		}
	}
}

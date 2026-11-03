using System;
using System.Collections.Generic;
using System.Linq;

namespace ModSwap;

public class PartOp
{
	public bool Hide;

	public double[] Move = new double[3];

	public double Scale = 1.0;

	public double[] Rot = new double[3];

	public bool IsDefault
	{
		get
		{
			if (!Hide && Move.All((double v) => v == 0.0) && Math.Abs(Scale - 1.0) < 1E-09)
			{
				return Rot.All((double v) => v == 0.0);
			}
			return false;
		}
	}

	public Dictionary<string, object> ToJson()
	{
		Dictionary<string, object> dictionary = new Dictionary<string, object>();
		if (Hide)
		{
			dictionary["hide"] = true;
		}
		dictionary["move"] = Move;
		dictionary["scale"] = Scale;
		dictionary["rot"] = Rot;
		return dictionary;
	}
}

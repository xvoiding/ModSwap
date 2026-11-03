using System;

namespace ModSwap;

public class ApiException : Exception
{
	public ApiException(string message)
		: base(message)
	{
	}
}

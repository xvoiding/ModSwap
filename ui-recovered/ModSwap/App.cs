using System;
using System.CodeDom.Compiler;
using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Threading;

namespace ModSwap;

public class App : Application
{
	private bool _contentLoaded;

	public static string LogDir
	{
		get
		{
			string text = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ModSwap");
			try
			{
				Directory.CreateDirectory(text);
			}
			catch
			{
			}
			return text;
		}
	}

	public static void Log(string text)
	{
		try
		{
			File.AppendAllText(System.IO.Path.Combine(LogDir, "modswap.log"), DateTime.Now.ToString("HH:mm:ss ") + text + Environment.NewLine);
		}
		catch
		{
		}
	}

	protected override void OnStartup(StartupEventArgs e)
	{
		//IL_000f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0019: Expected O, but got Unknown
		base.OnStartup(e);
		((Application)this).DispatcherUnhandledException += (DispatcherUnhandledExceptionEventHandler)delegate(object s, DispatcherUnhandledExceptionEventArgs a)
		{
			//IL_008d: Unknown result type (might be due to invalid IL or missing references)
			Log("UI crash: " + a.Exception);
			a.Handled = true;
			if (((Application)this).MainWindow is MainWindow mainWindow2 && ((FrameworkElement)mainWindow2).IsLoaded)
			{
				mainWindow2.Toast("Something went wrong: " + a.Exception.Message, ok: false);
			}
			else
			{
				MessageBox.Show("ModSwap couldn't start.\n\n" + a.Exception.Message + "\n\nDetails are in " + System.IO.Path.Combine(LogDir, "modswap.log"), "ModSwap", (MessageBoxButton)0, (MessageBoxImage)16);
				((Application)this).Shutdown(1);
			}
		};
		AppDomain.CurrentDomain.UnhandledException += delegate(object s, UnhandledExceptionEventArgs a)
		{
			Log("Fatal: " + a.ExceptionObject);
		};
		MainWindow mainWindow = (MainWindow)(object)(((Application)this).MainWindow = (Window)(object)new MainWindow());
		((Window)mainWindow).Show();
	}

	[DebuggerNonUserCode]
	[GeneratedCode("PresentationBuildTasks", "8.0.11.0")]
	public void InitializeComponent()
	{
		if (!_contentLoaded)
		{
			_contentLoaded = true;
			Uri uri = new Uri("/ModSwap;component/app.xaml", UriKind.Relative);
			Application.LoadComponent((object)this, uri);
		}
	}

	[STAThread]
	[DebuggerNonUserCode]
	[GeneratedCode("PresentationBuildTasks", "8.0.11.0")]
	public static void Main()
	{
		App app = new App();
		app.InitializeComponent();
		((Application)app).Run();
	}
}

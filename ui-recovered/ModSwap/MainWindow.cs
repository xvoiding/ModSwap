using System;
using System.CodeDom.Compiler;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Markup;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Media.Imaging;
using System.Windows.Media.Media3D;
using System.Windows.Shapes;
using System.Windows.Threading;
using Microsoft.Win32;

namespace ModSwap;

public class MainWindow : Window, IComponentConnector
{
	[Serializable]
	[CompilerGenerated]
	private sealed class _003C_003Ec
	{
		public static readonly _003C_003Ec _003C_003E9 = new _003C_003Ec();

		public static DragEventHandler _003C_003E9__7_5;

		public static Func<PartRow, int> _003C_003E9__39_48;

		public static DragEventHandler _003C_003E9__39_46;

		public static Func<JsonElement, string> _003C_003E9__40_0;

		public static Func<KeyValuePair<string, string>, string> _003C_003E9__47_0;

		public static Func<GameRow, bool> _003C_003E9__54_1;

		public static Func<GameRow, string> _003C_003E9__54_2;

		public static Func<GameRow, bool> _003C_003E9__54_4;

		public static Func<GameRow, bool> _003C_003E9__54_5;

		public static Func<GameRow, bool> _003C_003E9__56_0;

		public static Func<CharRow, bool> _003C_003E9__64_1;

		public static Func<CharRow, bool> _003C_003E9__64_2;

		public static Func<CharRow, bool> _003C_003E9__64_3;

		public static Func<CharRow, bool> _003C_003E9__64_4;

		public static Func<CharRow, bool> _003C_003E9__64_5;

		public static Func<CharRow, bool> _003C_003E9__64_6;

		public static Func<JsonElement, string> _003C_003E9__65_0;

		public static Func<JsonElement, string> _003C_003E9__65_9;

		public static Func<CharRow, bool> _003C_003E9__65_1;

		public static Func<CharRow, bool> _003C_003E9__65_2;

		public static Func<CharRow, bool> _003C_003E9__65_3;

		public static Func<CharRow, bool> _003C_003E9__65_4;

		public static Func<CharRow, bool> _003C_003E9__65_5;

		public static Func<CharRow, bool> _003C_003E9__65_6;

		public static Func<CharRow, bool> _003C_003E9__65_7;

		public static Func<string, bool> _003C_003E9__74_0;

		public static Func<JsonElement, int> _003C_003E9__75_0;

		public static Func<PartRow, bool> _003C_003E9__79_0;

		public static Func<PartRow, int> _003C_003E9__79_1;

		public static Func<char, bool> _003C_003E9__80_5;

		public static Func<JsonElement, string> _003C_003E9__87_0;

		public static RoutedEventHandler _003C_003E9__109_8;

		public static Func<JsonElement, bool> _003C_003E9__112_0;

		public static Func<JsonElement, string> _003C_003E9__112_1;

		public static Func<JsonElement, string> _003C_003E9__114_0;

		public static Func<MarketRow, bool> _003C_003E9__115_0;

		public static Func<MarketRow, string> _003C_003E9__115_2;

		public static Func<string, bool> _003C_003E9__115_3;

		public static Func<string, string> _003C_003E9__115_4;

		public static Func<MarketRow, bool> _003C_003E9__116_0;

		public static Func<MarketRow, bool> _003C_003E9__116_3;

		public static Func<MarketRow, string> _003C_003E9__116_4;

		public static Func<MarketRow, bool> _003C_003E9__117_0;

		public static Func<JsonElement, string> _003C_003E9__149_0;

		public static Func<char, bool> _003C_003E9__154_0;

		public static Func<ModRow, bool> _003C_003E9__171_0;

		public static Func<string, string> _003C_003E9__179_0;

		public static Func<string, bool> _003C_003E9__179_1;

		public static Func<GameRow, string> _003C_003E9__179_2;

		internal void _003CWireExtUi_003Eb__7_5(object s, DragEventArgs e)
		{
			e.Effects = (DragDropEffects)(e.Data.GetDataPresent(DataFormats.FileDrop) ? 1 : 0);
			((RoutedEventArgs)e).Handled = true;
		}

		internal int _003CWireUp_003Eb__39_48(PartRow p)
		{
			return p.Index;
		}

		internal void _003CWireUp_003Eb__39_46(object s, DragEventArgs e)
		{
			e.Effects = (DragDropEffects)(e.Data.GetDataPresent(DataFormats.FileDrop) ? 1 : 0);
			((RoutedEventArgs)e).Handled = true;
		}

		internal string _003CBoot__003Eb__40_0(JsonElement x)
		{
			return x.GetProperty("name").GetString();
		}

		internal string _003CSaveBroken_003Eb__47_0(KeyValuePair<string, string> kv)
		{
			return kv.Key + "\t" + kv.Value;
		}

		internal bool _003CApplyFilter_003Eb__54_1(GameRow g)
		{
			return g.Supported;
		}

		internal string _003CApplyFilter_003Eb__54_2(GameRow g)
		{
			return g.Name;
		}

		internal bool _003CApplyFilter_003Eb__54_4(GameRow g)
		{
			return !g.Supported;
		}

		internal bool _003CApplyFilter_003Eb__54_5(GameRow g)
		{
			return g.Supported;
		}

		internal bool _003CLoadArt_003Eb__56_0(GameRow r)
		{
			if (!r.ArtTried)
			{
				return r.Art == null;
			}
			return false;
		}

		internal bool _003CApplyCharFilter_003Eb__64_1(CharRow r)
		{
			return r.Hidden;
		}

		internal bool _003CApplyCharFilter_003Eb__64_2(CharRow r)
		{
			if (!r.Hidden)
			{
				return r.Cat == "character";
			}
			return false;
		}

		internal bool _003CApplyCharFilter_003Eb__64_3(CharRow r)
		{
			if (!r.Hidden)
			{
				return r.Cat == "vehicle";
			}
			return false;
		}

		internal bool _003CApplyCharFilter_003Eb__64_4(CharRow r)
		{
			if (!r.Hidden)
			{
				return r.Cat == "weapon";
			}
			return false;
		}

		internal bool _003CApplyCharFilter_003Eb__64_5(CharRow r)
		{
			if (!r.Hidden)
			{
				return r.Cat == "prop";
			}
			return false;
		}

		internal bool _003CApplyCharFilter_003Eb__64_6(CharRow r)
		{
			return !r.Hidden;
		}

		internal string _003CDetectChars_003Eb__65_0(JsonElement c)
		{
			return Regex.Replace(c.GetProperty("label").GetString() ?? "", "\\s{2}\\(.*\\)$", "");
		}

		internal string _003CDetectChars_003Eb__65_9(JsonElement x)
		{
			return x.GetString();
		}

		internal bool _003CDetectChars_003Eb__65_1(CharRow r)
		{
			return r.Hidden;
		}

		internal bool _003CDetectChars_003Eb__65_2(CharRow r)
		{
			return r.Cat.Length > 0;
		}

		internal bool _003CDetectChars_003Eb__65_3(CharRow r)
		{
			if (!r.Hidden)
			{
				return r.Cat == "character";
			}
			return false;
		}

		internal bool _003CDetectChars_003Eb__65_4(CharRow r)
		{
			if (!r.Hidden)
			{
				return r.Cat == "vehicle";
			}
			return false;
		}

		internal bool _003CDetectChars_003Eb__65_5(CharRow r)
		{
			if (!r.Hidden)
			{
				return r.Cat == "weapon";
			}
			return false;
		}

		internal bool _003CDetectChars_003Eb__65_6(CharRow r)
		{
			if (!r.Hidden)
			{
				return r.Cat == "prop";
			}
			return false;
		}

		internal bool _003CDetectChars_003Eb__65_7(CharRow r)
		{
			return !r.Hidden;
		}

		internal bool _003CUploadPaths_003Eb__74_0(string f)
		{
			return Wanted.Contains(Path.GetExtension(f));
		}

		internal int _003CFinishLoad_003Eb__75_0(JsonElement x)
		{
			return x.GetProperty("i").GetInt32();
		}

		internal bool _003COnPartClick_003Eb__79_0(PartRow p)
		{
			return p.On;
		}

		internal int _003COnPartClick_003Eb__79_1(PartRow p)
		{
			return p.Index;
		}

		internal bool _003CBuildSliders_003Eb__80_5(char ch)
		{
			if (!char.IsDigit(ch) && ch != '.' && ch != '-')
			{
				return ch == ',';
			}
			return true;
		}

		internal string _003CBuildTargets_003Eb__87_0(JsonElement x)
		{
			return Regex.Replace(x.GetString() ?? "", "^.*SK_NPC_|^.*SK_", "");
		}

		internal void _003CWireMarketUi_003Eb__109_8(object s, RoutedEventArgs e)
		{
			OpenUrl("https://sketchfab.com/settings/password");
		}

		internal bool _003CStrs_003Eb__112_0(JsonElement x)
		{
			return x.ValueKind == JsonValueKind.String;
		}

		internal string _003CStrs_003Eb__112_1(JsonElement x)
		{
			return x.GetString();
		}

		internal string _003CLoadMarket_003Eb__114_0(JsonElement x)
		{
			return x.GetString();
		}

		internal bool _003CBuildMarketChips_003Eb__115_0(MarketRow r)
		{
			return r.ForThisGame;
		}

		internal string _003CBuildMarketChips_003Eb__115_2(MarketRow r)
		{
			return r.Category;
		}

		internal bool _003CBuildMarketChips_003Eb__115_3(string c)
		{
			return !string.IsNullOrEmpty(c);
		}

		internal string _003CBuildMarketChips_003Eb__115_4(string c)
		{
			return c;
		}

		internal bool _003CApplyMarketFilter_003Eb__116_0(MarketRow r)
		{
			return r.ForThisGame;
		}

		internal bool _003CApplyMarketFilter_003Eb__116_3(MarketRow r)
		{
			return r.ForThisGame;
		}

		internal string _003CApplyMarketFilter_003Eb__116_4(MarketRow r)
		{
			return r.Name;
		}

		internal bool _003CLoadMarketPreviews_003Eb__117_0(MarketRow r)
		{
			return r.HasPreview;
		}

		internal string _003CPartsAfterFit_003Eb__149_0(JsonElement x)
		{
			return x.GetString();
		}

		internal bool _003CCommitBox_003Eb__154_0(char ch)
		{
			if (!char.IsDigit(ch) && ch != '.' && ch != '-')
			{
				return ch == ',';
			}
			return true;
		}

		internal bool _003CLoadMods_003Eb__171_0(ModRow x)
		{
			return x.Active;
		}

		internal string _003CSelfTest_003Eb__179_0(string x)
		{
			return x.Trim();
		}

		internal bool _003CSelfTest_003Eb__179_1(string x)
		{
			return x.Length > 0;
		}

		internal string _003CSelfTest_003Eb__179_2(GameRow g)
		{
			return g.Name + " [" + g.Label + "]";
		}
	}

	private bool extBusy;

	private readonly Api api = new Api();

	private readonly Backend backend = new Backend();

	private readonly Viewer3D viewer = new Viewer3D();

	private List<GameRow> allGames = new List<GameRow>();

	private GameRow cur;

	private bool charsReady;

	private int fam;

	private int target;

	private string sid = NewSid();

	private readonly List<string> files = new List<string>();

	private JsonElement? info;

	private List<int> parts = new List<int>();

	private string upAxis = "";

	private string fwdAxis = "";

	private JsonElement? fit;

	private bool installed;

	private bool installing;

	private int fseq;

	private bool suppress;

	private static readonly (string k, string label, double min, double max, string unit, double mult)[] SL = new(string, string, double, double, string, double)[10]
	{
		("scale", "Size", 40.0, 200.0, "%", 100.0),
		("width", "Width", 50.0, 200.0, "%", 100.0),
		("height", "Height", 50.0, 200.0, "%", 100.0),
		("depth", "Depth, front to back", 50.0, 200.0, "%", 100.0),
		("yaw", "Turn", -180.0, 180.0, "°", 1.0),
		("pitch", "Tilt forward / back", -60.0, 60.0, "°", 1.0),
		("roll", "Lean left / right", -60.0, 60.0, "°", 1.0),
		("dx", "Left / right", -40.0, 40.0, " cm", 1.0),
		("dy", "Forward / back", -40.0, 40.0, " cm", 1.0),
		("dz", "Up / down", -30.0, 30.0, " cm", 1.0)
	};

	private Dictionary<string, double> adj = Def();

	private Dictionary<string, double> last;

	private readonly Dictionary<string, Slider> sliders = new Dictionary<string, Slider>();

	private readonly Dictionary<string, TextBox> sliderVals = new Dictionary<string, TextBox>();

	private readonly DispatcherTimer fitTimer = new DispatcherTimer
	{
		Interval = TimeSpan.FromMilliseconds(380.0)
	};

	private readonly Dictionary<string, string> broken = new Dictionary<string, string>();

	private readonly SemaphoreSlim artGate = new SemaphoreSlim(4);

	private static readonly HashSet<string> Wanted = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
	{
		".fbx", ".obj", ".glb", ".gltf", ".vrm", ".dae", ".ply", ".stl", ".off", ".3mf",
		".x3d", ".wrl", ".blend", ".3ds", ".usd", ".usda", ".usdc", ".usdz", ".abc", ".zip",
		".png", ".jpg", ".jpeg", ".tga", ".bmp", ".dds", ".webp", ".tif", ".tiff", ".mtl",
		".bin"
	};

	private List<CharRow> allChars;

	private string lastModId = "";

	private List<MarketRow> marketAll = new List<MarketRow>();

	private string marketCat = "all";

	private bool marketBusy;

	private int marketGen;

	private string marketFolder = "";

	private string marketBundled = "";

	private bool sfMode;

	private bool sfConnected;

	private bool modeSuppress;

	private string sfUser = "";

	private string sfCur = "popular";

	private string sfCursor = "";

	private int sfGen;

	private readonly List<MarketRow> sfRows = new List<MarketRow>();

	private DispatcherTimer sfTimer;

	private bool unlimited;

	private bool matchPose;

	private const double MaxSlide = 1000.0;

	private readonly List<Slider> partSliderList = new List<Slider>();

	private readonly Dictionary<int, PartOp> autoOps = new Dictionary<int, PartOp>();

	private readonly List<CustomPart> customs = new List<CustomPart>();

	private string[] groupNames = new string[6] { "Torso", "Head", "Left arm", "Right arm", "Left leg", "Right leg" };

	private byte[] vgroup;

	private int vertN;

	private int selPart = -1;

	private bool partsBuilt;

	private string toolName = "";

	private bool[] lineSideA;

	private bool[] lineSideB;

	private bool lineFlipped;

	private CustomPart lineTarget;

	private int modCount;

	private bool anyOld;

	private bool modsMode;

	private string stDir;

	internal Grid Root;

	internal Button BtnMin;

	internal Button BtnMax;

	internal Button BtnClose;

	internal Button BtnScan;

	internal Button BtnAdd;

	internal Grid SearchRow;

	internal TextBox SearchBox;

	internal TextBlock SearchHint;

	internal RadioButton FilterAll;

	internal RadioButton FilterSwap;

	internal ListBox GameList;

	internal TextBlock LibFoot;

	internal Button BtnShowAll;

	internal Grid EmptyView;

	internal TextBlock HomeSub;

	internal Button BtnScan2;

	internal Button BtnAdd2;

	internal TextBox HomeSearch;

	internal TextBlock HomeSearchHint;

	internal ScrollViewer HomeScroll;

	internal ItemsControl GameGrid;

	internal TextBlock HomeEmpty;

	internal Button BtnShowAll2;

	internal Border HowCard;

	internal Button BtnDiag;

	internal TextBlock FormatsText;

	internal Grid WorkView;

	internal Button BtnBack;

	internal Button BtnMods;

	internal TextBlock GameTitle;

	internal TextBlock EngineText;

	internal Border SwapTag;

	internal TextBlock SwapTagText;

	internal TextBlock GamePath;

	internal Button BtnMarket;

	internal Button BtnExt;

	internal Button BtnRedetect;

	internal Button BtnRemove;

	internal Grid ModsView;

	internal Button BtnNewMod;

	internal ItemsControl ModList;

	internal Border OldInstallCard;

	internal Button BtnRemoveOld;

	internal Grid ExtView;

	internal TextBlock ExtIntro;

	internal Button BtnExtSwap;

	internal Grid ExtDrop;

	internal Rectangle ExtRect;

	internal SolidColorBrush ExtBrush;

	internal Border ExtBypass;

	internal TextBlock ExtBypassTitle;

	internal TextBlock ExtBypassText;

	internal TextBlock ExtEmpty;

	internal ItemsControl ExtList;

	internal Button BtnExtFolder;

	internal Button BtnReset2;

	internal Grid MarketView;

	internal TextBlock MarketIntro;

	internal Button BtnMarketBack;

	internal RadioButton MkLib;

	internal RadioButton MkSf;

	internal TextBox MarketSearch;

	internal TextBlock MarketSearchHint;

	internal WrapPanel MarketChips;

	internal Border SfConnect;

	internal TextBlock SfTitle;

	internal TextBlock SfText;

	internal StackPanel SfTokenRow;

	internal TextBox SfToken;

	internal TextBlock SfTokenHint;

	internal Button BtnSfConnect;

	internal Button BtnSfGet;

	internal Button BtnSfOff;

	internal TextBlock MarketNote;

	internal Border MarketEmpty;

	internal TextBlock MarketEmptyText;

	internal ItemsControl MarketList;

	internal Button BtnSfMore;

	internal Button BtnMarketFolder;

	internal Grid Wizard;

	internal ScrollViewer StepsScroll;

	internal Border Step1;

	internal TextBlock Num1;

	internal TextBlock Step1Title;

	internal TextBlock CharStatus;

	internal Grid CharSearchBox;

	internal TextBox CharSearch;

	internal TextBlock CharSearchHint;

	internal WrapPanel CharCats;

	internal RadioButton CatAll;

	internal RadioButton CatPeople;

	internal RadioButton CatVehicles;

	internal RadioButton CatWeapons;

	internal RadioButton CatObjects;

	internal ToggleButton CatHidden;

	internal TextBlock CharEmpty;

	internal ListBox CharList;

	internal Grid CharFoot;

	internal TextBlock CharCount;

	internal Button BtnRescan;

	internal Border Step2;

	internal TextBlock Num2;

	internal Button BtnClearModel;

	internal Grid DropZone;

	internal Rectangle DropRect;

	internal SolidColorBrush DropBrush;

	internal TextBlock DropTitle;

	internal TextBlock DropSub;

	internal ItemsControl FileChips;

	internal TextBlock ModelSum;

	internal Grid StatsPanel;

	internal TextBlock StatV;

	internal TextBlock StatT;

	internal TextBlock StatM;

	internal TextBlock StatX;

	internal ItemsControl Thumbs;

	internal Button BtnAdv;

	internal StackPanel AdvPanel;

	internal StackPanel PartsPanel;

	internal Button BtnPartsAll;

	internal Button BtnPartsNone;

	internal ItemsControl PartsList;

	internal Grid AxisPanel;

	internal TextBlock UpLabel;

	internal ComboBox UpCombo;

	internal TextBlock FwdLabel;

	internal ComboBox FwdCombo;

	internal Border Step3;

	internal TextBlock Num3;

	internal TextBlock FitHint;

	internal StackPanel FitControls;

	internal StackPanel TargetBox;

	internal TextBlock TargetLabel;

	internal WrapPanel TargetBar;

	internal Button BtnRotL;

	internal Button BtnRotR;

	internal Button BtnTurn;

	internal Button BtnReset;

	internal CheckBox ChkUnlimited;

	internal CheckBox ChkMatchPose;

	internal StackPanel SliderHost;

	internal Button BtnMore;

	internal StackPanel SliderMore;

	internal Button BtnPartsEdit;

	internal StackPanel PartsEditor;

	internal WrapPanel PartChips;

	internal ToggleButton TglBox;

	internal ToggleButton TglCut;

	internal Button BtnFlip;

	internal TextBlock ToolHint;

	internal StackPanel PartOps;

	internal CheckBox ChkHide;

	internal StackPanel PartSliders;

	internal Button BtnPartReset;

	internal Button BtnPartMirror;

	internal Button BtnPartRemove;

	internal Border Step4;

	internal TextBlock Num4;

	internal TextBlock InstallHint;

	internal StackPanel InstallControls;

	internal TextBox ModName;

	internal Button BtnInstall;

	internal Button BtnSave;

	internal Grid StagePanel;

	internal Border Stage0;

	internal Border Stage1;

	internal Border Stage2;

	internal Border Stage3;

	internal TextBlock LogText;

	internal Border DoneCard;

	internal Button BtnUndo;

	internal Grid VpHost;

	internal Border VpMouse;

	internal Canvas ToolCanvas;

	internal StackPanel Placeholder;

	internal TextBlock PlaceholderSub;

	internal RadioButton ViewFront;

	internal RadioButton ViewSide;

	internal RadioButton ViewTop;

	internal RadioButton ViewOrbit;

	internal ToggleButton TglOutline;

	internal ToggleButton TglModel;

	internal Border BusyPill;

	internal TextBlock BusyText;

	internal Grid BusyBar;

	internal Rectangle BusyRect;

	internal TranslateTransform BusyShift;

	internal TextBlock FwdInfo;

	internal StackPanel ToastHost;

	internal Grid Boot;

	internal TextBlock BootText;

	internal TranslateTransform BootShift;

	private bool _contentLoaded;

	private static string BrokenFile => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ModSwap", "broken.txt");

	private static string AppVer
	{
		get
		{
			Version version = typeof(MainWindow).Assembly.GetName().Version;
			if (!(version == null))
			{
				return version.Major + "." + version.Minor;
			}
			return "0";
		}
	}

	private void ShowExt()
	{
		modsMode = false;
		((UIElement)Wizard).Visibility = (Visibility)2;
		((UIElement)ModsView).Visibility = (Visibility)2;
		((UIElement)MarketView).Visibility = (Visibility)2;
		((UIElement)ExtView).Visibility = (Visibility)0;
		Anim.In((FrameworkElement)(object)ExtView, 300.0, 10.0);
		bool flag = cur != null && cur.Supported;
		((UIElement)BtnExtSwap).Visibility = (Visibility)((!flag) ? 2 : 0);
		((UIElement)BtnMods).Visibility = (Visibility)2;
		ExtIntro.Text = (flag ? "Downloaded a mod from Nexus Mods or somewhere else? Drop it below and ModSwap puts every file in the right place. You can switch it off or remove it any time." : "ModSwap can't change character models in this game yet, but you can still add mods you downloaded. Drop one below and ModSwap puts every file in the right place. You can switch it off or remove it any time.");
	}

	private async Task LoadExt(GameRow g)
	{
		try
		{
			JsonElement jsonElement = await api.Get("/api/ext_mods?game=" + Uri.EscapeDataString(g.Id));
			if (cur == null || cur.Id != g.Id)
			{
				return;
			}
			List<ExtRow> list = new List<ExtRow>();
			foreach (JsonElement item in jsonElement.GetProperty("mods").EnumerateArray())
			{
				long @int = item.GetProperty("size").GetInt64();
				int int2 = item.GetProperty("files").GetInt32();
				DateTimeOffset dateTimeOffset = DateTimeOffset.FromUnixTimeSeconds((long)item.GetProperty("time").GetDouble()).ToLocalTime();
				list.Add(new ExtRow
				{
					Id = item.GetProperty("id").GetString(),
					Name = item.GetProperty("name").GetString(),
					Enabled = item.GetProperty("enabled").GetBoolean(),
					Sub = int2 + ((int2 == 1) ? " file" : " files") + "  ·  " + ((double)@int / 1048576.0).ToString("0.#") + " MB  ·  added " + dateTimeOffset.ToString("MMM d")
				});
			}
			ExtList.ItemsSource = list;
			((UIElement)ExtEmpty).Visibility = (Visibility)((list.Count != 0) ? 2 : 0);
			JsonElement property = jsonElement.GetProperty("bypass");
			bool boolean = property.GetProperty("needed").GetBoolean();
			bool boolean2 = property.GetProperty("present").GetBoolean();
			if (boolean)
			{
				((UIElement)ExtBypass).Visibility = (Visibility)0;
				ExtBypassTitle.Text = (boolean2 ? "Signature check: patched ✓" : "One extra step for this game");
				ExtBypassText.Text = (boolean2 ? "A signature bypass is installed, so the game will load mods from the mods folder." : "This game checks that every file is signed by the developer, so it ignores mods until a small patch called \"UTOC Signature Bypass\" is installed. Download it from this game's page on Nexus Mods, then drop its .zip here like any other mod. You only do this once.");
			}
			else
			{
				((UIElement)ExtBypass).Visibility = (Visibility)2;
			}
			((UIElement)BtnExtFolder).Visibility = (Visibility)((!jsonElement.GetProperty("can_install").GetBoolean()) ? 2 : 0);
		}
		catch (Exception ex)
		{
			App.Log("ext: " + ex);
		}
	}

	private void BrowseExt()
	{
		//IL_0011: Unknown result type (might be due to invalid IL or missing references)
		//IL_0016: Unknown result type (might be due to invalid IL or missing references)
		//IL_0021: Unknown result type (might be due to invalid IL or missing references)
		//IL_0028: Unknown result type (might be due to invalid IL or missing references)
		//IL_0034: Expected O, but got Unknown
		if (cur != null && !extBusy)
		{
			OpenFileDialog val = new OpenFileDialog
			{
				Title = "Pick the mod file(s)",
				Multiselect = true,
				Filter = "Mods (*.zip, *.pak, *.utoc, *.ucas)|*.zip;*.pak;*.utoc;*.ucas|All files|*.*"
			};
			if (((CommonDialog)val).ShowDialog((Window)(object)this).GetValueOrDefault())
			{
				ExtInstall(((FileDialog)val).FileNames);
			}
		}
	}

	private async Task ExtInstall(string[] paths)
	{
		if (cur == null || extBusy || paths == null || paths.Length == 0)
		{
			return;
		}
		GameRow g = cur;
		extBusy = true;
		_ = ExtIntro.Text;
		((UIElement)ExtDrop).IsEnabled = false;
		ExtIntro.Text = "Adding the mod... big mods can take a minute.";
		try
		{
			bool code = false;
			while (true)
			{
				JsonElement jsonElement = await api.Post("/api/ext_install", new Dictionary<string, object>
				{
					{ "game", g.Id },
					{ "paths", paths },
					{ "allow_code", code }
				});
				if (jsonElement.TryGetProperty("needs_confirm", out var value) && value.ValueKind == JsonValueKind.String)
				{
					if (code)
					{
						break;
					}
					if ((int)MessageBox.Show((Window)(object)this, value.GetString() + "\n\nAdd it anyway?", "ModSwap", (MessageBoxButton)4, (MessageBoxImage)48) != 6)
					{
						Toast("Cancelled. Nothing was changed.");
						break;
					}
					code = true;
					continue;
				}
				string @string = jsonElement.GetProperty("mod").GetProperty("name").GetString();
				Toast(@string + " added. Launch the game!");
				foreach (JsonElement item in jsonElement.GetProperty("notes").EnumerateArray())
				{
					Toast(item.GetString(), ok: false);
				}
				break;
			}
			if (cur != null && cur.Id == g.Id)
			{
				await LoadExt(g);
			}
		}
		catch (Exception ex)
		{
			Toast(Friendly(ex.Message).Item1, ok: false);
			App.Log("ext install: " + ex);
		}
		finally
		{
			extBusy = false;
			((UIElement)ExtDrop).IsEnabled = true;
			if (cur != null && cur.Id == g.Id)
			{
				ShowExtIntroFor(g);
			}
		}
	}

	private void ShowExtIntroFor(GameRow g)
	{
		ExtIntro.Text = (g.Supported ? "Downloaded a mod from Nexus Mods or somewhere else? Drop it below and ModSwap puts every file in the right place. You can switch it off or remove it any time." : "ModSwap can't change character models in this game yet, but you can still add mods you downloaded. Drop one below and ModSwap puts every file in the right place. You can switch it off or remove it any time.");
	}

	private async void OnExtClick(object sender, RoutedEventArgs e)
	{
		object originalSource = e.OriginalSource;
		Button val = (Button)((originalSource is Button) ? originalSource : null);
		if (val == null)
		{
			return;
		}
		object dataContext = ((FrameworkElement)val).DataContext;
		if (!(dataContext is ExtRow row) || cur == null)
		{
			return;
		}
		string text = ((FrameworkElement)val).Tag as string;
		GameRow g = cur;
		try
		{
			if (text == "toggle")
			{
				await api.Post("/api/ext_toggle", new Dictionary<string, object>
				{
					{ "game", g.Id },
					{ "id", row.Id }
				});
				Toast(row.Name + (row.Enabled ? " is off" : " is on"));
				await LoadExt(g);
			}
			else if (text == "remove" && (int)MessageBox.Show((Window)(object)this, "Remove \"" + row.Name + "\" from the game?\nIts files are deleted and anything it replaced is put back.", "ModSwap", (MessageBoxButton)1, (MessageBoxImage)32) == 1)
			{
				await api.Post("/api/ext_remove", new Dictionary<string, object>
				{
					{ "game", g.Id },
					{ "id", row.Id }
				});
				Toast("Removed " + row.Name);
				await LoadExt(g);
			}
		}
		catch (Exception ex)
		{
			Toast(Friendly(ex.Message).Item1, ok: false);
			App.Log("ext action: " + ex);
		}
	}

	private void WireExtUi()
	{
		//IL_0012: Unknown result type (might be due to invalid IL or missing references)
		//IL_001c: Expected O, but got Unknown
		//IL_0029: Unknown result type (might be due to invalid IL or missing references)
		//IL_0033: Expected O, but got Unknown
		//IL_0040: Unknown result type (might be due to invalid IL or missing references)
		//IL_004a: Expected O, but got Unknown
		//IL_0057: Unknown result type (might be due to invalid IL or missing references)
		//IL_0061: Expected O, but got Unknown
		//IL_006e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0078: Expected O, but got Unknown
		//IL_0085: Unknown result type (might be due to invalid IL or missing references)
		//IL_008f: Expected O, but got Unknown
		//IL_00c6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d0: Expected O, but got Unknown
		//IL_00dd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e7: Expected O, but got Unknown
		//IL_00f4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00fe: Expected O, but got Unknown
		//IL_010b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0115: Expected O, but got Unknown
		//IL_00a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b4: Expected O, but got Unknown
		((UIElement)ExtList).AddHandler(ButtonBase.ClickEvent, (Delegate)new RoutedEventHandler(OnExtClick));
		((ButtonBase)BtnExt).Click += (RoutedEventHandler)async delegate
		{
			if (cur != null)
			{
				ShowExt();
				await LoadExt(cur);
			}
		};
		((ButtonBase)BtnExtSwap).Click += (RoutedEventHandler)async delegate
		{
			if (cur != null)
			{
				((UIElement)ExtView).Visibility = (Visibility)2;
				await RouteMods(cur);
			}
		};
		((UIElement)ExtDrop).MouseLeftButtonUp += (MouseButtonEventHandler)delegate
		{
			BrowseExt();
		};
		((UIElement)ExtDrop).DragEnter += (DragEventHandler)delegate
		{
			ExtDragState(over: true);
		};
		((UIElement)ExtDrop).DragLeave += (DragEventHandler)delegate
		{
			ExtDragState(over: false);
		};
		Grid extDrop = ExtDrop;
		object obj = _003C_003Ec._003C_003E9__7_5;
		if (obj == null)
		{
			DragEventHandler val = delegate(object s, DragEventArgs e)
			{
				e.Effects = (DragDropEffects)(e.Data.GetDataPresent(DataFormats.FileDrop) ? 1 : 0);
				((RoutedEventArgs)e).Handled = true;
			};
			_003C_003Ec._003C_003E9__7_5 = val;
			obj = (object)val;
		}
		((UIElement)extDrop).DragOver += (DragEventHandler)obj;
		((UIElement)ExtDrop).Drop += (DragEventHandler)delegate(object s, DragEventArgs e)
		{
			ExtDragState(over: false);
			((RoutedEventArgs)e).Handled = true;
			if (e.Data.GetDataPresent(DataFormats.FileDrop))
			{
				ExtInstall((string[])e.Data.GetData(DataFormats.FileDrop));
			}
		};
		((ButtonBase)BtnDiag).Click += (RoutedEventHandler)delegate
		{
			try
			{
				string path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ModSwap", "modswap.log");
				string text = (File.Exists(path) ? string.Join("\n", File.ReadAllLines(path).Reverse().Take(250)
					.Reverse()) : "(no log yet)");
				Clipboard.SetText(string.Concat("ModSwap " + AppVer + "  ·  " + Environment.OSVersion?.ToString() + "  ·  game: " + ((cur == null) ? "none" : (cur.Name + " [" + cur.Label + "]")), "\n\n", text));
				Toast("Copied. Paste it in a message to whoever is helping you.");
			}
			catch (Exception ex3)
			{
				Toast("Couldn't copy: " + ex3.Message, ok: false);
			}
		};
		((ButtonBase)BtnReset2).Click += (RoutedEventHandler)async delegate
		{
			if (cur != null)
			{
				GameRow g = cur;
				if ((int)MessageBox.Show((Window)(object)this, "Take every mod ModSwap added out of " + g.Name + "?\nThe game goes back to how it was before you used ModSwap. Your saved character mods stay in ModSwap.", "ModSwap", (MessageBoxButton)1, (MessageBoxImage)32) == 1)
				{
					try
					{
						int @int = (await api.Post("/api/reset_game", new Dictionary<string, object> { { "game", g.Id } })).GetProperty("removed").GetInt32();
						Toast((@int == 0) ? "Nothing to remove. The game is already clean." : (g.Name + " is back to normal."));
						installed = false;
						if (cur != null && cur.Id == g.Id)
						{
							await LoadExt(g);
						}
					}
					catch (Exception ex2)
					{
						Toast(Friendly(ex2.Message).Item1, ok: false);
						App.Log("reset: " + ex2);
					}
				}
			}
		};
		((ButtonBase)BtnExtFolder).Click += (RoutedEventHandler)async delegate
		{
			if (cur == null)
			{
				return;
			}
			try
			{
				await api.Post("/api/ext_open", new Dictionary<string, object> { { "game", cur.Id } });
			}
			catch (Exception ex)
			{
				Toast(Friendly(ex.Message).Item1, ok: false);
			}
		};
	}

	private void ExtDragState(bool over)
	{
		//IL_0025: Unknown result type (might be due to invalid IL or missing references)
		//IL_000f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0069: Unknown result type (might be due to invalid IL or missing references)
		//IL_0051: Unknown result type (might be due to invalid IL or missing references)
		//IL_006e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0078: Expected O, but got Unknown
		Anim.Brush(ExtBrush, over ? Color.FromRgb((byte)244, (byte)244, (byte)244) : Color.FromRgb((byte)58, (byte)58, (byte)58), 160.0);
		((Shape)ExtRect).Fill = (Brush)new SolidColorBrush(over ? Color.FromArgb((byte)20, byte.MaxValue, byte.MaxValue, byte.MaxValue) : Color.FromArgb((byte)0, byte.MaxValue, byte.MaxValue, byte.MaxValue));
	}

	[DllImport("dwmapi.dll")]
	private static extern int DwmSetWindowAttribute(nint hwnd, int attr, ref int value, int size);

	private static Dictionary<string, double> Def()
	{
		return new Dictionary<string, double>
		{
			{ "scale", 1.0 },
			{ "width", 1.0 },
			{ "height", 1.0 },
			{ "depth", 1.0 },
			{ "yaw", 0.0 },
			{ "pitch", 0.0 },
			{ "roll", 0.0 },
			{ "dx", 0.0 },
			{ "dy", 0.0 },
			{ "dz", 0.0 }
		};
	}

	private static string NewSid()
	{
		return Guid.NewGuid().ToString("N").Substring(0, 12);
	}

	public MainWindow()
	{
		//IL_0085: Unknown result type (might be due to invalid IL or missing references)
		//IL_008a: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a3: Expected O, but got Unknown
		//IL_020e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0218: Expected O, but got Unknown
		InitializeComponent();
		((Panel)VpHost).Children.Insert(0, (UIElement)(object)viewer.VP);
		viewer.Attach((UIElement)(object)VpMouse);
		LoadBroken();
		BuildSliders();
		WireUp();
		WirePartsUi();
		WireModsUi();
		WireExtUi();
		WireMarketUi();
		fitTimer.Tick += delegate
		{
			fitTimer.Stop();
			RequestFit(first: false);
		};
		((FrameworkElement)this).Loaded += (RoutedEventHandler)async delegate
		{
			await Boot_();
		};
		((Window)this).Closing += delegate
		{
			backend.Dispose();
		};
	}

	protected override void OnSourceInitialized(EventArgs e)
	{
		//IL_0008: Unknown result type (might be due to invalid IL or missing references)
		((Window)this).OnSourceInitialized(e);
		try
		{
			IntPtr handle = new WindowInteropHelper((Window)(object)this).Handle;
			int value = 2;
			int value2 = 1;
			int value3 = 2236962;
			DwmSetWindowAttribute(handle, 33, ref value, 4);
			DwmSetWindowAttribute(handle, 20, ref value2, 4);
			DwmSetWindowAttribute(handle, 34, ref value3, 4);
		}
		catch
		{
		}
	}

	private void WireUp()
	{
		//IL_000d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0017: Expected O, but got Unknown
		//IL_0024: Unknown result type (might be due to invalid IL or missing references)
		//IL_002e: Expected O, but got Unknown
		//IL_003b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0045: Expected O, but got Unknown
		//IL_0064: Unknown result type (might be due to invalid IL or missing references)
		//IL_006e: Expected O, but got Unknown
		//IL_007b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0085: Expected O, but got Unknown
		//IL_0092: Unknown result type (might be due to invalid IL or missing references)
		//IL_009c: Expected O, but got Unknown
		//IL_00a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b3: Expected O, but got Unknown
		//IL_00c0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ca: Expected O, but got Unknown
		//IL_00d7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e1: Expected O, but got Unknown
		//IL_00ee: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f8: Expected O, but got Unknown
		//IL_0105: Unknown result type (might be due to invalid IL or missing references)
		//IL_010f: Expected O, but got Unknown
		//IL_011c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0126: Expected O, but got Unknown
		//IL_0133: Unknown result type (might be due to invalid IL or missing references)
		//IL_013d: Expected O, but got Unknown
		//IL_014a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0154: Expected O, but got Unknown
		//IL_0161: Unknown result type (might be due to invalid IL or missing references)
		//IL_016b: Expected O, but got Unknown
		//IL_0178: Unknown result type (might be due to invalid IL or missing references)
		//IL_0182: Expected O, but got Unknown
		//IL_018f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0199: Expected O, but got Unknown
		//IL_01a6: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b0: Expected O, but got Unknown
		//IL_01bd: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c7: Expected O, but got Unknown
		//IL_01d4: Unknown result type (might be due to invalid IL or missing references)
		//IL_01de: Expected O, but got Unknown
		//IL_01eb: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f5: Expected O, but got Unknown
		//IL_0202: Unknown result type (might be due to invalid IL or missing references)
		//IL_020c: Expected O, but got Unknown
		//IL_024e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0258: Expected O, but got Unknown
		//IL_026f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0279: Expected O, but got Unknown
		//IL_0286: Unknown result type (might be due to invalid IL or missing references)
		//IL_0290: Expected O, but got Unknown
		//IL_029d: Unknown result type (might be due to invalid IL or missing references)
		//IL_02a7: Expected O, but got Unknown
		//IL_02b4: Unknown result type (might be due to invalid IL or missing references)
		//IL_02be: Expected O, but got Unknown
		//IL_02cb: Unknown result type (might be due to invalid IL or missing references)
		//IL_02d5: Expected O, but got Unknown
		//IL_02e2: Unknown result type (might be due to invalid IL or missing references)
		//IL_02ec: Expected O, but got Unknown
		//IL_02f9: Unknown result type (might be due to invalid IL or missing references)
		//IL_0303: Expected O, but got Unknown
		//IL_0315: Unknown result type (might be due to invalid IL or missing references)
		//IL_031f: Expected O, but got Unknown
		//IL_032c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0336: Expected O, but got Unknown
		//IL_0343: Unknown result type (might be due to invalid IL or missing references)
		//IL_034d: Expected O, but got Unknown
		//IL_035a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0364: Expected O, but got Unknown
		//IL_0371: Unknown result type (might be due to invalid IL or missing references)
		//IL_037b: Expected O, but got Unknown
		//IL_0388: Unknown result type (might be due to invalid IL or missing references)
		//IL_0392: Expected O, but got Unknown
		//IL_039f: Unknown result type (might be due to invalid IL or missing references)
		//IL_03a9: Expected O, but got Unknown
		//IL_03b6: Unknown result type (might be due to invalid IL or missing references)
		//IL_03c0: Expected O, but got Unknown
		//IL_03cd: Unknown result type (might be due to invalid IL or missing references)
		//IL_03d7: Expected O, but got Unknown
		//IL_03e4: Unknown result type (might be due to invalid IL or missing references)
		//IL_03ee: Expected O, but got Unknown
		//IL_03fb: Unknown result type (might be due to invalid IL or missing references)
		//IL_0405: Expected O, but got Unknown
		//IL_0412: Unknown result type (might be due to invalid IL or missing references)
		//IL_041c: Expected O, but got Unknown
		//IL_0429: Unknown result type (might be due to invalid IL or missing references)
		//IL_0433: Expected O, but got Unknown
		//IL_0440: Unknown result type (might be due to invalid IL or missing references)
		//IL_044a: Expected O, but got Unknown
		//IL_0457: Unknown result type (might be due to invalid IL or missing references)
		//IL_0461: Expected O, but got Unknown
		//IL_046e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0478: Expected O, but got Unknown
		//IL_0485: Unknown result type (might be due to invalid IL or missing references)
		//IL_048f: Expected O, but got Unknown
		//IL_04a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_04a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_04af: Expected O, but got Unknown
		((ButtonBase)BtnMin).Click += (RoutedEventHandler)delegate
		{
			((Window)this).WindowState = (WindowState)1;
		};
		((ButtonBase)BtnMax).Click += (RoutedEventHandler)delegate
		{
			//IL_0002: Unknown result type (might be due to invalid IL or missing references)
			//IL_0008: Invalid comparison between Unknown and I4
			((Window)this).WindowState = (WindowState)(((int)((Window)this).WindowState != 2) ? 2 : 0);
		};
		((ButtonBase)BtnClose).Click += (RoutedEventHandler)delegate
		{
			((Window)this).Close();
		};
		((Window)this).StateChanged += delegate
		{
			//IL_0007: Unknown result type (might be due to invalid IL or missing references)
			//IL_000d: Invalid comparison between Unknown and I4
			//IL_0028: Unknown result type (might be due to invalid IL or missing references)
			//IL_0018: Unknown result type (might be due to invalid IL or missing references)
			//IL_0039: Unknown result type (might be due to invalid IL or missing references)
			//IL_003f: Invalid comparison between Unknown and I4
			((FrameworkElement)Root).Margin = (((int)((Window)this).WindowState == 2) ? new Thickness(7.0) : new Thickness(0.0));
			((ContentControl)BtnMax).Content = (((int)((Window)this).WindowState == 2) ? "\ue923" : "\ue922");
		};
		((ButtonBase)BtnScan).Click += (RoutedEventHandler)async delegate
		{
			await ScanSteam(loud: true);
		};
		((ButtonBase)BtnScan2).Click += (RoutedEventHandler)async delegate
		{
			await ScanSteam(loud: true);
		};
		((ButtonBase)BtnAdd).Click += (RoutedEventHandler)async delegate
		{
			await AddGame();
		};
		((ButtonBase)BtnAdd2).Click += (RoutedEventHandler)async delegate
		{
			await AddGame();
		};
		((TextBoxBase)HomeSearch).TextChanged += (TextChangedEventHandler)delegate
		{
			((UIElement)HomeSearchHint).Visibility = (Visibility)((HomeSearch.Text.Length != 0) ? 2 : 0);
			ApplyFilter();
		};
		((ButtonBase)BtnShowAll2).Click += (RoutedEventHandler)delegate
		{
			if (((ToggleButton)FilterSwap).IsChecked.GetValueOrDefault())
			{
				((ToggleButton)FilterAll).IsChecked = true;
			}
			else
			{
				((ToggleButton)FilterSwap).IsChecked = true;
			}
		};
		((ButtonBase)BtnBack).Click += (RoutedEventHandler)delegate
		{
			GoHome();
		};
		((UIElement)GameGrid).PreviewMouseLeftButtonUp += (MouseButtonEventHandler)delegate(object s, MouseButtonEventArgs e)
		{
			object originalSource = ((RoutedEventArgs)e).OriginalSource;
			for (DependencyObject val2 = (DependencyObject)((originalSource is DependencyObject) ? originalSource : null); val2 != null; val2 = ((val2 is Visual || val2 is Visual3D) ? VisualTreeHelper.GetParent(val2) : LogicalTreeHelper.GetParent(val2)))
			{
				FrameworkElement val3 = (FrameworkElement)(object)((val2 is FrameworkElement) ? val2 : null);
				if (val3 != null && val3.DataContext is GameRow g2)
				{
					SelectGame(g2);
					((RoutedEventArgs)e).Handled = true;
					break;
				}
			}
		};
		((TextBoxBase)SearchBox).TextChanged += (TextChangedEventHandler)delegate
		{
			((UIElement)SearchHint).Visibility = (Visibility)((SearchBox.Text.Length != 0) ? 2 : 0);
			ApplyFilter();
		};
		((ToggleButton)FilterAll).Checked += (RoutedEventHandler)delegate
		{
			ApplyFilter();
		};
		((ToggleButton)FilterSwap).Checked += (RoutedEventHandler)delegate
		{
			ApplyFilter();
		};
		((ButtonBase)BtnShowAll).Click += (RoutedEventHandler)delegate
		{
			if (((ToggleButton)FilterSwap).IsChecked.GetValueOrDefault())
			{
				((ToggleButton)FilterAll).IsChecked = true;
			}
			else
			{
				((ToggleButton)FilterSwap).IsChecked = true;
			}
		};
		((ButtonBase)BtnAdv).Click += (RoutedEventHandler)delegate
		{
			//IL_0006: Unknown result type (might be due to invalid IL or missing references)
			//IL_000c: Invalid comparison between Unknown and I4
			bool flag2 = (int)((UIElement)AdvPanel).Visibility > 0;
			((UIElement)AdvPanel).Visibility = (Visibility)((!flag2) ? 2 : 0);
			((ContentControl)BtnAdv).Content = (flag2 ? "Advanced  −" : "Advanced  +");
			if (flag2)
			{
				Anim.In((FrameworkElement)(object)AdvPanel, 260.0, 8.0);
			}
		};
		((ButtonBase)BtnMore).Click += (RoutedEventHandler)delegate
		{
			//IL_0006: Unknown result type (might be due to invalid IL or missing references)
			//IL_000c: Invalid comparison between Unknown and I4
			bool flag = (int)((UIElement)SliderMore).Visibility > 0;
			((UIElement)SliderMore).Visibility = (Visibility)((!flag) ? 2 : 0);
			((ContentControl)BtnMore).Content = (flag ? "Fine tune  −" : "Fine tune  +");
			if (flag)
			{
				Anim.In((FrameworkElement)(object)SliderMore, 260.0, 8.0);
			}
		};
		((Selector)GameList).SelectionChanged += (SelectionChangedEventHandler)delegate
		{
			if (!suppress && ((Selector)GameList).SelectedItem is GameRow g)
			{
				SelectGame(g);
			}
		};
		((ButtonBase)BtnRedetect).Click += (RoutedEventHandler)async delegate
		{
			await Redetect();
		};
		((ButtonBase)BtnRemove).Click += (RoutedEventHandler)async delegate
		{
			await RemoveGame();
		};
		((ButtonBase)BtnRescan).Click += (RoutedEventHandler)async delegate
		{
			await DetectChars();
		};
		((TextBoxBase)CharSearch).TextChanged += (TextChangedEventHandler)delegate
		{
			((UIElement)CharSearchHint).Visibility = (Visibility)((CharSearch.Text.Length != 0) ? 2 : 0);
			ApplyCharFilter();
		};
		RadioButton[] array = (RadioButton[])(object)new RadioButton[5] { CatAll, CatPeople, CatVehicles, CatWeapons, CatObjects };
		for (int i = 0; i < array.Length; i++)
		{
			((ToggleButton)array[i]).Checked += (RoutedEventHandler)delegate
			{
				if (CatHidden.IsChecked.GetValueOrDefault())
				{
					CatHidden.IsChecked = false;
				}
				else
				{
					ApplyCharFilter();
				}
			};
		}
		CatHidden.Checked += (RoutedEventHandler)delegate
		{
			RadioButton[] array2 = (RadioButton[])(object)new RadioButton[5] { CatAll, CatPeople, CatVehicles, CatWeapons, CatObjects };
			for (int j = 0; j < array2.Length; j++)
			{
				((ToggleButton)array2[j]).IsChecked = false;
			}
			ApplyCharFilter();
		};
		CatHidden.Unchecked += (RoutedEventHandler)delegate
		{
			if (!CatHidden.IsChecked.GetValueOrDefault() && !((ToggleButton)CatAll).IsChecked.GetValueOrDefault() && !((ToggleButton)CatPeople).IsChecked.GetValueOrDefault() && !((ToggleButton)CatVehicles).IsChecked.GetValueOrDefault() && !((ToggleButton)CatWeapons).IsChecked.GetValueOrDefault() && !((ToggleButton)CatObjects).IsChecked.GetValueOrDefault())
			{
				((ToggleButton)CatAll).IsChecked = true;
			}
		};
		((Selector)CharList).SelectionChanged += (SelectionChangedEventHandler)delegate
		{
			if (!suppress && ((Selector)CharList).SelectedItem is CharRow charRow)
			{
				fam = charRow.Index;
				target = 0;
				last = null;
				fit = null;
				viewer.Clear();
				ShowPlaceholder(on: true);
				UpdateSteps();
				ResetInstallUi();
				if (info.HasValue)
				{
					RequestFit(first: true);
				}
			}
		};
		((UIElement)DropZone).MouseLeftButtonUp += (MouseButtonEventHandler)delegate
		{
			BrowseModel();
		};
		((ButtonBase)BtnClearModel).Click += (RoutedEventHandler)async delegate
		{
			await ClearModel();
		};
		((Selector)UpCombo).SelectionChanged += (SelectionChangedEventHandler)delegate
		{
			if (!suppress && ((Selector)UpCombo).SelectedIndex >= 0)
			{
				upAxis = ((((Selector)UpCombo).SelectedIndex == 0) ? "" : ((string)((Selector)UpCombo).SelectedItem));
				RequestFit(first: false);
			}
		};
		((Selector)FwdCombo).SelectionChanged += (SelectionChangedEventHandler)delegate
		{
			if (!suppress && ((Selector)FwdCombo).SelectedIndex >= 0)
			{
				fwdAxis = ((((Selector)FwdCombo).SelectedIndex == 0) ? "" : ((string)((Selector)FwdCombo).SelectedItem));
				RequestFit(first: false);
			}
		};
		((UIElement)PartsList).AddHandler(ButtonBase.ClickEvent, (Delegate)new RoutedEventHandler(OnPartClick));
		((ButtonBase)BtnPartsAll).Click += (RoutedEventHandler)delegate
		{
			if (PartsList.ItemsSource is List<PartRow> list2)
			{
				foreach (PartRow item in list2)
				{
					item.On = true;
				}
				PartsList.ItemsSource = null;
				PartsList.ItemsSource = list2;
				parts = list2.Select((PartRow p) => p.Index).ToList();
				RequestFit(first: false);
			}
		};
		((ButtonBase)BtnPartsNone).Click += (RoutedEventHandler)delegate
		{
			if (PartsList.ItemsSource is List<PartRow> list)
			{
				foreach (PartRow item2 in list)
				{
					item2.On = false;
				}
				PartsList.ItemsSource = null;
				PartsList.ItemsSource = list;
				parts = new List<int>();
				Toast("Tick at least one part", ok: false);
			}
		};
		((ButtonBase)BtnRotL).Click += (RoutedEventHandler)delegate
		{
			Rotate(-90.0);
		};
		((ButtonBase)BtnRotR).Click += (RoutedEventHandler)delegate
		{
			Rotate(90.0);
		};
		((ButtonBase)BtnTurn).Click += (RoutedEventHandler)delegate
		{
			Rotate(180.0);
		};
		((ButtonBase)BtnReset).Click += (RoutedEventHandler)delegate
		{
			adj = Def();
			SyncSliders();
			LiveUpdate();
		};
		((ButtonBase)BtnInstall).Click += (RoutedEventHandler)async delegate
		{
			await Install();
		};
		((ButtonBase)BtnUndo).Click += (RoutedEventHandler)async delegate
		{
			await Undo();
		};
		((ToggleButton)ViewFront).Checked += (RoutedEventHandler)delegate
		{
			viewer.SetView("front");
		};
		((ToggleButton)ViewSide).Checked += (RoutedEventHandler)delegate
		{
			viewer.SetView("side");
		};
		((ToggleButton)ViewTop).Checked += (RoutedEventHandler)delegate
		{
			viewer.SetView("top");
		};
		((ToggleButton)ViewOrbit).Checked += (RoutedEventHandler)delegate
		{
			viewer.SetView("orbit");
		};
		((ButtonBase)TglOutline).Click += (RoutedEventHandler)delegate
		{
			viewer.SetOutline(TglOutline.IsChecked.GetValueOrDefault());
		};
		((ButtonBase)TglModel).Click += (RoutedEventHandler)delegate
		{
			viewer.SetModel(TglModel.IsChecked.GetValueOrDefault());
		};
		((UIElement)DropZone).DragEnter += (DragEventHandler)delegate
		{
			DragState(over: true);
		};
		((UIElement)DropZone).DragLeave += (DragEventHandler)delegate
		{
			DragState(over: false);
		};
		object obj = _003C_003Ec._003C_003E9__39_46;
		if (obj == null)
		{
			DragEventHandler val = delegate(object s, DragEventArgs e)
			{
				e.Effects = (DragDropEffects)(e.Data.GetDataPresent(DataFormats.FileDrop) ? 1 : 0);
				((RoutedEventArgs)e).Handled = true;
			};
			_003C_003Ec._003C_003E9__39_46 = val;
			obj = (object)val;
		}
		((UIElement)this).DragOver += (DragEventHandler)obj;
	}

	private async Task Boot_()
	{
		Anim.Sweep(BootShift, -50.0, 120.0, 1100.0);
		Anim.In((FrameworkElement)(object)Root, 420.0, 0.0);
		try
		{
			BootText.Text = "starting the engine";
			Api api = this.api;
			api.Base = await backend.Start();
			BootText.Text = "loading your library";
			try
			{
				List<string> values = (from x in (await this.api.Get("/api/formats")).GetProperty("formats").EnumerateArray()
					select x.GetProperty("name").GetString()).ToList();
				FormatsText.Text = "Imports  " + string.Join("  ·  ", values);
			}
			catch
			{
			}
			await LoadGames();
			if (allGames.Count == 0)
			{
				await ScanSteam(loud: false);
			}
			Anim.Out_((FrameworkElement)(object)Boot, 380.0);
			if (File.Exists(Path.Combine(Backend.AppDir, "selftest.txt")))
			{
				SelfTest();
			}
		}
		catch (Exception ex)
		{
			App.Log("Boot failed: " + ex);
			BootText.Text = "Couldn't start the engine.\n" + ex.Message;
			BootText.TextWrapping = (TextWrapping)2;
			((FrameworkElement)BootText).MaxWidth = 520.0;
			BootText.TextAlignment = (TextAlignment)2;
			((Animatable)BootShift).BeginAnimation(TranslateTransform.XProperty, (AnimationTimeline)null);
		}
	}

	private void LoadBroken()
	{
		try
		{
			string[] array = File.ReadAllLines(BrokenFile);
			if (array.Length == 0 || array[0] != "#v\t" + AppVer)
			{
				return;
			}
			foreach (string item in array.Skip(1))
			{
				string[] array2 = item.Split('\t');
				if (array2.Length == 2)
				{
					broken[array2[0]] = array2[1];
				}
			}
		}
		catch
		{
		}
	}

	private void SaveBroken()
	{
		try
		{
			Directory.CreateDirectory(Path.GetDirectoryName(BrokenFile));
			File.WriteAllLines(BrokenFile, new string[1] { "#v\t" + AppVer }.Concat(broken.Select((KeyValuePair<string, string> kv) => kv.Key + "\t" + kv.Value)));
		}
		catch
		{
		}
	}

	private static (string, bool) Friendly(string m)
	{
		m = m ?? "";
		if (m.Contains("mesh layout"))
		{
			Match match = Regex.Match(m, "report: (.+)");
			return ("ModSwap can't read this game's character files yet." + (match.Success ? ("\nI saved a report you can send me:\n" + match.Groups[1].Value.Trim()) : ""), true);
		}
		if (m.Contains("AES key"))
		{
			return ("This game's files are encrypted and ModSwap doesn't have the right key for it.", true);
		}
		if (m.Contains("IoStore"))
		{
			return ("This game keeps its characters in IoStore containers (.utoc/.ucas) and ModSwap couldn't open them.", true);
		}
		if (m.Contains("retoc") && (m.Contains("not found") || m.Contains("download")))
		{
			return ("ModSwap needs to download a small tool the first time (retoc), and couldn't. Check your internet and try again.", false);
		}
		if (m.Contains("retoc") && m.Contains("failed"))
		{
			return ("ModSwap couldn't read this game's containers. Make sure the game is fully installed (Steam: verify game files), then try again.", false);
		}
		if (m.Contains("Permission") || m.Contains("Access is denied") || m.Contains("being used by another"))
		{
			return ("Windows wouldn't let ModSwap change a file. Close the game (and anything else using it) and try again.", false);
		}
		if (m.Contains("no .pak files"))
		{
			return ("This game packs its files in a way ModSwap can't read yet.", true);
		}
		if (m.Contains("repak") && m.Contains("failed"))
		{
			return ("ModSwap couldn't open this game's files. They may be encrypted or in an unsupported pak version.", true);
		}
		if (m.Contains("repak not found") || m.Contains("automatic download"))
		{
			return ("ModSwap needs to download a small tool the first time, and couldn't. Check your internet and try again.", false);
		}
		if (m.Contains("not supported yet"))
		{
			return ("ModSwap can't edit this kind of game yet.", true);
		}
		string text = m.Split('\n')[0].Trim();
		return ((text.Length > 140) ? (text.Substring(0, 140) + "...") : text, false);
	}

	private void MarkBroken(GameRow g, string text, bool permanent)
	{
		//IL_0026: Unknown result type (might be due to invalid IL or missing references)
		//IL_002c: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00eb: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f5: Expected O, but got Unknown
		CharStatus.Text = text;
		((UIElement)CharStatus).Visibility = (Visibility)0;
		ListBox charList = CharList;
		Grid charFoot = CharFoot;
		Visibility visibility = (Visibility)2;
		((UIElement)charFoot).Visibility = (Visibility)2;
		((UIElement)charList).Visibility = visibility;
		charsReady = false;
		fit = null;
		viewer.Clear();
		ShowPlaceholder(on: true);
		if (permanent && g != null)
		{
			broken[g.Id] = text;
			SaveBroken();
			g.Supported = false;
			g.Sub = g.Label + "  ·  can't edit yet";
			SwapTagText.Text = "not supported";
			SwapTag.Background = (Brush)(object)Brushes.Transparent;
			SwapTag.BorderThickness = new Thickness(1.0);
			SwapTagText.Foreground = (Brush)new SolidColorBrush(Color.FromRgb((byte)142, (byte)142, (byte)142));
			ApplyFilter();
			if (cur != null && cur.Id == g.Id)
			{
				ShowExt();
				LoadExt(g);
			}
		}
		UpdateSteps();
	}

	public void Toast(string msg, bool ok = true)
	{
		//IL_00a7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ac: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b3: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ec: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f6: Unknown result type (might be due to invalid IL or missing references)
		//IL_011b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0125: Unknown result type (might be due to invalid IL or missing references)
		//IL_0134: Unknown result type (might be due to invalid IL or missing references)
		//IL_013b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0140: Unknown result type (might be due to invalid IL or missing references)
		//IL_014a: Expected O, but got Unknown
		//IL_014a: Unknown result type (might be due to invalid IL or missing references)
		//IL_016a: Unknown result type (might be due to invalid IL or missing references)
		//IL_015d: Unknown result type (might be due to invalid IL or missing references)
		//IL_016f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0179: Expected O, but got Unknown
		//IL_0179: Unknown result type (might be due to invalid IL or missing references)
		//IL_0183: Unknown result type (might be due to invalid IL or missing references)
		//IL_018d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0199: Expected O, but got Unknown
		//IL_0199: Unknown result type (might be due to invalid IL or missing references)
		//IL_019e: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a6: Expected O, but got Unknown
		//IL_01ac: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b1: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c6: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c7: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d1: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f6: Unknown result type (might be due to invalid IL or missing references)
		//IL_0200: Unknown result type (might be due to invalid IL or missing references)
		//IL_0210: Expected O, but got Unknown
		//IL_0217: Unknown result type (might be due to invalid IL or missing references)
		//IL_021c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0223: Unknown result type (might be due to invalid IL or missing references)
		//IL_022a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0239: Unknown result type (might be due to invalid IL or missing references)
		//IL_024d: Expected O, but got Unknown
		//IL_0298: Unknown result type (might be due to invalid IL or missing references)
		//IL_029d: Unknown result type (might be due to invalid IL or missing references)
		//IL_02c4: Expected O, but got Unknown
		foreach (Border item in ((IEnumerable)((Panel)ToastHost).Children).OfType<Border>().ToList())
		{
			if (((FrameworkElement)item).Tag as string == msg)
			{
				return;
			}
		}
		List<Border> list = ((IEnumerable)((Panel)ToastHost).Children).OfType<Border>().ToList();
		for (int i = 0; i < list.Count - 1; i++)
		{
			((Panel)ToastHost).Children.Remove((UIElement)(object)list[i]);
		}
		Border b = new Border
		{
			Tag = msg,
			CornerRadius = new CornerRadius(12.0),
			Padding = new Thickness(16.0, 11.0, 18.0, 11.0),
			Margin = new Thickness(0.0, 8.0, 0.0, 0.0),
			MaxWidth = 420.0,
			Background = (Brush)new SolidColorBrush(Color.FromRgb((byte)20, (byte)20, (byte)20)),
			BorderBrush = (Brush)new SolidColorBrush(ok ? Color.FromRgb((byte)80, (byte)80, (byte)80) : Color.FromRgb((byte)200, (byte)200, (byte)200)),
			BorderThickness = new Thickness(1.0),
			HorizontalAlignment = (HorizontalAlignment)2
		};
		StackPanel val = new StackPanel
		{
			Orientation = (Orientation)0
		};
		((Panel)val).Children.Add((UIElement)new TextBlock
		{
			Text = (ok ? "✓" : "!"),
			FontWeight = FontWeights.Bold,
			Margin = new Thickness(0.0, 0.0, 10.0, 0.0),
			Foreground = (Brush)(object)Brushes.White
		});
		((Panel)val).Children.Add((UIElement)new TextBlock
		{
			Text = msg,
			TextWrapping = (TextWrapping)2,
			MaxWidth = 340.0,
			FontSize = 12.5
		});
		((Decorator)b).Child = (UIElement)(object)val;
		((Panel)ToastHost).Children.Add((UIElement)(object)b);
		Anim.In((FrameworkElement)(object)b, 300.0, 16.0);
		DispatcherTimer t = new DispatcherTimer
		{
			Interval = TimeSpan.FromSeconds(ok ? 3.6 : 6.5)
		};
		t.Tick += delegate
		{
			t.Stop();
			Anim.Out_((FrameworkElement)(object)b, 260.0, delegate
			{
				((Panel)ToastHost).Children.Remove((UIElement)(object)b);
			});
		};
		t.Start();
	}

	private static GameRow ToRow(JsonElement g)
	{
		bool boolean = g.GetProperty("supported").GetBoolean();
		string @string = g.GetProperty("label").GetString();
		JsonElement value;
		return new GameRow
		{
			Id = g.GetProperty("id").GetString(),
			Name = g.GetProperty("name").GetString(),
			Label = @string,
			Supported = boolean,
			Engine = (g.TryGetProperty("engine", out value) ? value.GetString() : ""),
			Root = g.GetProperty("root").GetString(),
			Sub = @string + (boolean ? "" : "  ·  mod files only")
		};
	}

	private async Task LoadGames()
	{
		SetGames((await api.Get("/api/games")).GetProperty("games"));
	}

	private void SetGames(JsonElement arr)
	{
		allGames = arr.EnumerateArray().Select(ToRow).ToList();
		foreach (GameRow allGame in allGames)
		{
			if (broken.ContainsKey(allGame.Id))
			{
				allGame.Supported = false;
				allGame.Sub = allGame.Label + "  ·  can't edit yet";
			}
		}
		ApplyFilter();
	}

	private void ApplyFilter()
	{
		//IL_02c5: Unknown result type (might be due to invalid IL or missing references)
		//IL_02cb: Invalid comparison between Unknown and I4
		if (GameList == null)
		{
			return;
		}
		string q = (HomeSearch.Text ?? "").Trim().ToLowerInvariant();
		List<GameRow> list = (from g in allGames
			where (q.Length == 0 || g.Name.ToLowerInvariant().Contains(q) || g.Label.ToLowerInvariant().Contains(q)) && (!((ToggleButton)FilterSwap).IsChecked.GetValueOrDefault() || g.Supported)
			orderby g.Supported descending, g.Name
			select g).ToList();
		suppress = true;
		((ItemsControl)GameList).ItemsSource = list;
		if (cur != null)
		{
			((Selector)GameList).SelectedItem = list.FirstOrDefault((GameRow g) => g.Id == cur.Id);
		}
		suppress = false;
		bool valueOrDefault = ((ToggleButton)FilterAll).IsChecked.GetValueOrDefault();
		int num = allGames.Count((GameRow g) => !g.Supported);
		LibFoot.Text = ((allGames.Count == 0) ? "Runs entirely on your PC" : (valueOrDefault ? (allGames.Count + " games") : (allGames.Count((GameRow g) => g.Supported) + " games you can swap")));
		((UIElement)BtnShowAll).Visibility = (Visibility)((num <= 0) ? 2 : 0);
		((ContentControl)BtnShowAll).Content = (valueOrDefault ? "Hide unsupported" : ("Show all (" + num + " more)"));
		GameGrid.ItemsSource = list;
		((UIElement)BtnShowAll2).Visibility = (Visibility)((num <= 0 || q.Length != 0) ? 2 : 0);
		((ContentControl)BtnShowAll2).Content = (valueOrDefault ? "Hide games ModSwap can't edit" : ("Show the " + num + " games ModSwap can't edit yet"));
		((UIElement)HomeEmpty).Visibility = (Visibility)((allGames.Count != 0) ? 2 : 0);
		HomeEmpty.Text = ((allGames.Count == 0) ? "No games yet. Hit Find my games (Steam, Epic, GOG, Xbox), or Add game and pick the game's .exe." : "");
		if (allGames.Count > 0 && list.Count == 0)
		{
			((UIElement)HomeEmpty).Visibility = (Visibility)0;
			HomeEmpty.Text = ((q.Length > 0) ? "No games match that." : "Nothing swappable here yet.");
		}
		((UIElement)HomeSearch).Visibility = (Visibility)(((int)((UIElement)HomeSearchHint).Visibility != 2 && allGames.Count <= 0) ? 2 : 0);
		if (allGames.Count == 0)
		{
			((UIElement)HomeSearchHint).Visibility = (Visibility)2;
		}
		LoadArt(list);
		if (cur == null)
		{
			((UIElement)EmptyView).Visibility = (Visibility)0;
			((UIElement)WorkView).Visibility = (Visibility)2;
		}
	}

	private async Task LoadArt(List<GameRow> rows)
	{
		foreach (GameRow item in rows.Where((GameRow r) => !r.ArtTried && r.Art == null).ToList())
		{
			item.ArtTried = true;
			GameRow row = item;
			Task.Run(async delegate
			{
				await artGate.WaitAsync();
				try
				{
					byte[] bytes = await api.GetBytes("/api/art?id=" + Uri.EscapeDataString(row.Id));
					if (bytes != null)
					{
						await ((DispatcherObject)this).Dispatcher.InvokeAsync((Action)delegate
						{
							//IL_0000: Unknown result type (might be due to invalid IL or missing references)
							//IL_0006: Expected O, but got Unknown
							try
							{
								BitmapImage val = new BitmapImage();
								val.BeginInit();
								val.CacheOption = (BitmapCacheOption)1;
								val.DecodePixelWidth = 480;
								val.StreamSource = new MemoryStream(bytes);
								val.EndInit();
								((Freezable)val).Freeze();
								row.Art = (ImageSource)(object)val;
							}
							catch
							{
							}
						});
					}
				}
				catch
				{
				}
				finally
				{
					artGate.Release();
				}
			});
		}
		await Task.CompletedTask;
	}

	private void GoHome()
	{
		if (cur != null)
		{
			cur = null;
			viewer.Clear();
			((UIElement)WorkView).Visibility = (Visibility)2;
			suppress = true;
			((Selector)GameList).SelectedItem = null;
			suppress = false;
			Anim.In((FrameworkElement)(object)EmptyView, 340.0, 12.0);
		}
	}

	private async Task ScanSteam(bool loud)
	{
		Button btnScan = BtnScan;
		bool isEnabled = (((UIElement)BtnScan2).IsEnabled = false);
		((UIElement)btnScan).IsEnabled = isEnabled;
		try
		{
			JsonElement jsonElement = await api.Post("/api/scan_steam");
			SetGames(jsonElement.GetProperty("games"));
			int @int = jsonElement.GetProperty("new").GetInt32();
			if (loud)
			{
				Toast((@int > 0) ? ("Found " + @int + " new game" + ((@int > 1) ? "s" : "")) : ((allGames.Count == 0) ? "No games found. Try Add game and pick the game's .exe." : "Library is up to date"));
			}
		}
		catch (Exception ex)
		{
			Toast(Friendly(ex.Message).Item1, ok: false);
		}
		finally
		{
			Button btnScan2 = BtnScan;
			isEnabled = (((UIElement)BtnScan2).IsEnabled = true);
			((UIElement)btnScan2).IsEnabled = isEnabled;
		}
	}

	private async Task AddGame()
	{
		OpenFileDialog val = new OpenFileDialog
		{
			Title = "Pick the game's .exe",
			Filter = "Game (*.exe)|*.exe|All files|*.*"
		};
		if (!((CommonDialog)val).ShowDialog((Window)(object)this).GetValueOrDefault())
		{
			return;
		}
		try
		{
			JsonElement jsonElement = await api.Post("/api/add", new Dictionary<string, object> { 
			{
				"exe",
				((FileDialog)val).FileName
			} });
			SetGames(jsonElement.GetProperty("games"));
			GameRow g = ToRow(jsonElement.GetProperty("game"));
			Toast("Added " + g.Name + " (" + g.Label + ")");
			cur = allGames.FirstOrDefault((GameRow x) => x.Id == g.Id);
			ApplyFilter();
			if (cur != null)
			{
				SelectGame(cur);
			}
		}
		catch (Exception ex)
		{
			Toast(Friendly(ex.Message).Item1, ok: false);
		}
	}

	private async Task RemoveGame()
	{
		if (cur == null || (int)MessageBox.Show((Window)(object)this, "Remove " + cur.Name + " from your library? (Nothing is deleted from the game.)", "ModSwap", (MessageBoxButton)1, (MessageBoxImage)32) != 1)
		{
			return;
		}
		try
		{
			JsonElement jsonElement = await api.Post("/api/remove", new Dictionary<string, object> { { "game", cur.Id } });
			cur = null;
			SetGames(jsonElement.GetProperty("games"));
			((UIElement)WorkView).Visibility = (Visibility)2;
			Anim.In((FrameworkElement)(object)EmptyView);
		}
		catch (Exception ex)
		{
			Toast(Friendly(ex.Message).Item1, ok: false);
		}
	}

	private async Task Redetect()
	{
		if (cur == null)
		{
			return;
		}
		try
		{
			GameRow g = ToRow((await api.Post("/api/redetect", new Dictionary<string, object> { { "game", cur.Id } })).GetProperty("game"));
			int num = allGames.FindIndex((GameRow x) => x.Id == g.Id);
			if (num >= 0)
			{
				allGames[num] = g;
			}
			cur = g;
			ApplyFilter();
			ShowGame(g, animate: false);
			Toast("Engine: " + g.Label);
			if (g.Supported && !charsReady)
			{
				await DetectChars();
			}
		}
		catch (Exception ex)
		{
			Toast(Friendly(ex.Message).Item1, ok: false);
		}
	}

	private void SelectGame(GameRow g)
	{
		//IL_000e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0014: Invalid comparison between Unknown and I4
		if (cur == null)
		{
			_ = 1;
		}
		else
			_ = (int)((UIElement)WorkView).Visibility > 0;
		cur = g;
		charsReady = false;
		fam = 0;
		target = 0;
		last = null;
		fit = null;
		installed = false;
		viewer.Clear();
		ShowPlaceholder(on: true);
		ResetInstallUi();
		suppress = true;
		((ItemsControl)CharList).ItemsSource = null;
		suppress = false;
		ShowGame(g, animate: true);
		ResetEdits();
		modCount = 0;
		anyOld = false;
		ShowWizard();
		RouteMods(g);
		if (!g.Supported)
		{
			ShowExt();
			LoadExt(g);
		}
		if (g.Supported)
		{
			DetectChars();
		}
	}

	private void ShowGame(GameRow g, bool animate)
	{
		//IL_0090: Unknown result type (might be due to invalid IL or missing references)
		//IL_0095: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00dc: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00eb: Expected O, but got Unknown
		//IL_011f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0124: Unknown result type (might be due to invalid IL or missing references)
		//IL_0291: Unknown result type (might be due to invalid IL or missing references)
		//IL_0298: Unknown result type (might be due to invalid IL or missing references)
		GameTitle.Text = g.Name;
		EngineText.Text = g.Label;
		GamePath.Text = g.Root;
		SwapTagText.Text = (g.Supported ? "swappable" : (broken.ContainsKey(g.Id) ? "not supported" : "mod files only"));
		SwapTag.Background = (Brush)((!g.Supported) ? ((object)Brushes.Transparent) : ((object)new SolidColorBrush(Color.FromRgb((byte)244, (byte)244, (byte)244))));
		SwapTag.BorderThickness = (g.Supported ? new Thickness(0.0) : new Thickness(1.0));
		SwapTag.BorderBrush = (Brush)new SolidColorBrush(Color.FromRgb((byte)51, (byte)51, (byte)51));
		((UIElement)BtnMarket).Visibility = (Visibility)((!g.Supported) ? 2 : 0);
		SwapTagText.Foreground = (Brush)(g.Supported ? ((object)Brushes.Black) : ((object)new SolidColorBrush(Color.FromRgb((byte)142, (byte)142, (byte)142))));
		((UIElement)EmptyView).Visibility = (Visibility)2;
		if (animate)
		{
			((UIElement)WorkView).Visibility = (Visibility)0;
			Anim.In((FrameworkElement)(object)WorkView, 380.0, 18.0);
			(FrameworkElement, double)[] array = new(FrameworkElement, double)[4]
			{
				((FrameworkElement)(object)Step1, 60.0),
				((FrameworkElement)(object)Step2, 120.0),
				((FrameworkElement)(object)Step3, 180.0),
				((FrameworkElement)(object)Step4, 240.0)
			};
			for (int i = 0; i < array.Length; i++)
			{
				var (el, delay) = array[i];
				Anim.In(el, 420.0, 16.0, delay);
			}
		}
		else
		{
			((UIElement)WorkView).Visibility = (Visibility)0;
		}
		if (!g.Supported)
		{
			CharStatus.Text = (broken.ContainsKey(g.Id) ? broken[g.Id] : ("Detected " + g.Label + ". ModSwap can swap models in Unreal Engine and Unity games for now."));
			ListBox charList = CharList;
			Grid charFoot = CharFoot;
			Visibility visibility = (Visibility)2;
			((UIElement)charFoot).Visibility = (Visibility)2;
			((UIElement)charList).Visibility = visibility;
		}
		UpdateSteps();
	}

	private void ApplyCharFilter()
	{
		if (allChars != null)
		{
			string q = CharSearch.Text.Trim().ToLowerInvariant();
			bool valueOrDefault = CatHidden.IsChecked.GetValueOrDefault();
			IEnumerable<CharRow> source = ((q.Length > 0) ? allChars.Where((CharRow r) => r.Label.ToLowerInvariant().Contains(q) || r.Sub.ToLowerInvariant().Contains(q)) : (valueOrDefault ? allChars.Where((CharRow r) => r.Hidden) : (((ToggleButton)CatPeople).IsChecked.GetValueOrDefault() ? allChars.Where((CharRow r) => !r.Hidden && r.Cat == "character") : (((ToggleButton)CatVehicles).IsChecked.GetValueOrDefault() ? allChars.Where((CharRow r) => !r.Hidden && r.Cat == "vehicle") : (((ToggleButton)CatWeapons).IsChecked.GetValueOrDefault() ? allChars.Where((CharRow r) => !r.Hidden && r.Cat == "weapon") : ((!((ToggleButton)CatObjects).IsChecked.GetValueOrDefault()) ? allChars.Where((CharRow r) => !r.Hidden) : allChars.Where((CharRow r) => !r.Hidden && r.Cat == "prop")))))));
			List<CharRow> list = source.ToList();
			CharRow charRow = ((Selector)CharList).SelectedItem as CharRow;
			bool flag = suppress;
			suppress = true;
			((ItemsControl)CharList).ItemsSource = list;
			if (charRow != null && list.Contains(charRow))
			{
				((Selector)CharList).SelectedItem = charRow;
			}
			suppress = flag;
			if (!flag && ((Selector)CharList).SelectedItem == null && list.Count > 0 && CharSearch.Text.Trim().Length == 0)
			{
				((Selector)CharList).SelectedIndex = 0;
			}
			((UIElement)CharEmpty).Visibility = (Visibility)((list.Count != 0) ? 2 : 0);
			((UIElement)CharList).Visibility = (Visibility)((list.Count == 0) ? 2 : 0);
		}
	}

	private async Task DetectChars()
	{
		if (cur == null || !cur.Supported)
		{
			return;
		}
		string id = cur.Id;
		charsReady = false;
		fit = null;
		ListBox charList = CharList;
		Grid charFoot = CharFoot;
		Visibility visibility = (Visibility)2;
		((UIElement)charFoot).Visibility = (Visibility)2;
		((UIElement)charList).Visibility = visibility;
		((UIElement)CharStatus).Visibility = (Visibility)0;
		CharStatus.Text = "Reading the game files...";
		UpdateSteps();
		try
		{
			JsonElement jsonElement = await api.Post("/api/characters", new Dictionary<string, object> { { "game", id } });
			JsonElement jsonElement2 = await api.Job(jsonElement.GetProperty("job").GetString(), delegate(List<string> lines)
			{
				if (cur != null && cur.Id == id && lines.Count > 0)
				{
					CharStatus.Text = lines[lines.Count - 1];
				}
			});
			if (cur == null || cur.Id != id)
			{
				return;
			}
			List<CharRow> list = new List<CharRow>();
			int i = 0;
			bool flag = cur.Engine == "unity";
			Step1Title.Text = (flag ? "Model to replace" : "Character");
			List<string> rawNames = (from c in jsonElement2.GetProperty("characters").EnumerateArray()
				select Regex.Replace(c.GetProperty("label").GetString() ?? "", "\\s{2}\\(.*\\)$", "")).ToList();
			foreach (JsonElement item in jsonElement2.GetProperty("characters").EnumerateArray())
			{
				string.Join(", ", from x in item.GetProperty("body").EnumerateArray()
					select x.GetString());
				list.Add(new CharRow
				{
					Index = item.GetProperty("index").GetInt32(),
					Label = (flag ? item.GetProperty("label").GetString() : ((rawNames.Count((string n) => n == rawNames[i]) > 1) ? item.GetProperty("label").GetString() : rawNames[i])),
					Sub = (item.TryGetProperty("note", out var value) ? (value.GetString() ?? "") : ""),
					Cat = ((item.TryGetProperty("cat", out var value2) && value2.ValueKind == JsonValueKind.String) ? value2.GetString() : ""),
					Hidden = (item.TryGetProperty("hidden", out var value3) && value3.ValueKind == JsonValueKind.True)
				});
				i++;
			}
			jsonElement2.GetProperty("items").GetArrayLength();
			if (list.Count == 0)
			{
				CharStatus.Text = "No swappable characters found in this game.";
				UpdateSteps();
				return;
			}
			charsReady = true;
			allChars = list;
			int num = list.Count((CharRow r) => r.Hidden);
			int num2 = list.Count - num;
			suppress = true;
			CharSearch.Text = "";
			((ToggleButton)CatAll).IsChecked = true;
			CatHidden.IsChecked = false;
			suppress = false;
			bool flag2 = flag && list.Any((CharRow r) => r.Cat.Length > 0);
			((UIElement)CharCats).Visibility = (Visibility)((!flag2 || list.Count <= 8) ? 2 : 0);
			((ContentControl)CatHidden).Content = ((num > 0) ? ("Hidden  " + num) : "Hidden");
			((UIElement)CatHidden).Visibility = (Visibility)((num <= 0) ? 2 : 0);
			((UIElement)CatPeople).Visibility = (Visibility)((!list.Any((CharRow r) => !r.Hidden && r.Cat == "character")) ? 2 : 0);
			((UIElement)CatVehicles).Visibility = (Visibility)((!list.Any((CharRow r) => !r.Hidden && r.Cat == "vehicle")) ? 2 : 0);
			((UIElement)CatWeapons).Visibility = (Visibility)((!list.Any((CharRow r) => !r.Hidden && r.Cat == "weapon")) ? 2 : 0);
			((UIElement)CatObjects).Visibility = (Visibility)((!list.Any((CharRow r) => !r.Hidden && r.Cat == "prop")) ? 2 : 0);
			List<CharRow> list2 = (flag2 ? list.Where((CharRow r) => !r.Hidden).ToList() : list);
			if (list2.Count == 0)
			{
				list2 = list;
			}
			suppress = true;
			((ItemsControl)CharList).ItemsSource = list2;
			((Selector)CharList).SelectedIndex = 0;
			suppress = false;
			((UIElement)CharSearchBox).Visibility = (Visibility)((list.Count <= 8) ? 2 : 0);
			fam = list2[0].Index;
			((UIElement)CharStatus).Visibility = (Visibility)2;
			((UIElement)CharEmpty).Visibility = (Visibility)2;
			JsonElement value4;
			int num3 = ((jsonElement2.TryGetProperty("rigged", out value4) && value4.ValueKind == JsonValueKind.Number) ? value4.GetInt32() : (-1));
			CharCount.Text = (flag2 ? (num2 + ((num2 == 1) ? " model" : " models") + ((num3 > 0) ? ("  ·  " + num3 + " characters") : "") + ((num > 0) ? ("  ·  " + num + " hidden") : "")) : (list.Count + ((!flag) ? ((list.Count == 1) ? " character" : " characters") : ((list.Count == 1) ? " model" : " models")) + ((flag && num3 > 0) ? ("  ·  " + num3 + " characters") : "")));
			if (flag && num3 < 0)
			{
				Toast("The engine files in your ModSwap folder are older than the app. Replace the whole ModSwap folder with the latest zip so characters show up.", ok: false);
			}
			else if (flag && num3 == 0)
			{
				Toast("No rigged characters were found in this game's files.", ok: false);
			}
			Anim.In((FrameworkElement)(object)CharList, 320.0, 10.0);
			Anim.In((FrameworkElement)(object)CharFoot, 320.0, 6.0, 120.0);
			UpdateSteps();
			if (info.HasValue)
			{
				await RequestFit(first: true);
			}
		}
		catch (Exception ex)
		{
			if (cur != null && cur.Id == id)
			{
				App.Log("characters: " + ex);
				var (text, permanent) = Friendly(ex.Message);
				MarkBroken(cur, text, permanent);
			}
		}
	}

	private void UpdateSteps()
	{
		bool flag = cur != null && cur.Supported;
		SetStep(Step1, Num1, "1", unlocked: true, charsReady);
		SetStep(Step2, Num2, "2", flag && charsReady, info.HasValue);
		SetStep(Step3, Num3, "3", flag && charsReady && info.HasValue, fit.HasValue);
		SetStep(Step4, Num4, "4", flag && fit.HasValue, installed);
		((UIElement)FitHint).Visibility = (Visibility)((flag && charsReady && info.HasValue) ? 2 : 0);
		((UIElement)FitControls).Visibility = (Visibility)((!flag || !charsReady || !info.HasValue) ? 2 : 0);
		((UIElement)InstallHint).Visibility = (Visibility)(fit.HasValue ? 2 : 0);
		((UIElement)InstallControls).Visibility = (Visibility)((!fit.HasValue) ? 2 : 0);
	}

	private void SetStep(Border b, TextBlock num, string n, bool unlocked, bool done)
	{
		double num2 = (unlocked ? 1.0 : 0.38);
		if (Math.Abs(((UIElement)b).Opacity - num2) > 0.01 && ((FrameworkElement)this).IsLoaded)
		{
			Anim.Fade((UIElement)(object)b, num2, 320.0);
		}
		else
		{
			((UIElement)b).Opacity = num2;
		}
		((UIElement)b).IsHitTestVisible = unlocked;
		num.Text = (done ? "✓" : n);
	}

	private void ShowPlaceholder(bool on)
	{
		//IL_0033: Unknown result type (might be due to invalid IL or missing references)
		if (on)
		{
			((UIElement)Placeholder).Visibility = (Visibility)0;
			Anim.Fade((UIElement)(object)Placeholder, 1.0, 250.0);
		}
		else if ((int)((UIElement)Placeholder).Visibility == 0)
		{
			Anim.Out_((FrameworkElement)(object)Placeholder, 220.0);
		}
	}

	private void SetBusy(bool on, string text = null)
	{
		if (text != null)
		{
			BusyText.Text = text;
		}
		Anim.Fade((UIElement)(object)BusyPill, on ? 1 : 0, 220.0);
		Anim.Fade((UIElement)(object)BusyBar, on ? 1 : 0, 220.0);
		if (on)
		{
			Anim.Sweep(BusyShift, -180.0, Math.Max(400.0, ((FrameworkElement)VpHost).ActualWidth), 1100.0);
		}
		else
		{
			((Animatable)BusyShift).BeginAnimation(TranslateTransform.XProperty, (AnimationTimeline)null);
		}
	}

	private void BrowseModel()
	{
		//IL_0009: Unknown result type (might be due to invalid IL or missing references)
		//IL_000e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0019: Unknown result type (might be due to invalid IL or missing references)
		//IL_0020: Unknown result type (might be due to invalid IL or missing references)
		//IL_002c: Expected O, but got Unknown
		if (cur != null)
		{
			OpenFileDialog val = new OpenFileDialog
			{
				Title = "Pick your model and textures",
				Multiselect = true,
				Filter = "Models, textures, zips|*.fbx;*.obj;*.glb;*.gltf;*.vrm;*.dae;*.ply;*.stl;*.off;*.3mf;*.x3d;*.wrl;*.blend;*.3ds;*.usd;*.usda;*.usdc;*.usdz;*.abc;*.zip;*.png;*.jpg;*.jpeg;*.tga;*.bmp;*.dds;*.webp;*.mtl|All files|*.*"
			};
			if (((CommonDialog)val).ShowDialog((Window)(object)this).GetValueOrDefault())
			{
				UploadPaths(((FileDialog)val).FileNames);
			}
		}
	}

	private void DragState(bool over)
	{
		//IL_0025: Unknown result type (might be due to invalid IL or missing references)
		//IL_000f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0069: Unknown result type (might be due to invalid IL or missing references)
		//IL_0051: Unknown result type (might be due to invalid IL or missing references)
		//IL_006e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0078: Expected O, but got Unknown
		Anim.Brush(DropBrush, over ? Color.FromRgb((byte)244, (byte)244, (byte)244) : Color.FromRgb((byte)58, (byte)58, (byte)58), 160.0);
		((Shape)DropRect).Fill = (Brush)new SolidColorBrush(over ? Color.FromArgb((byte)20, byte.MaxValue, byte.MaxValue, byte.MaxValue) : Color.FromArgb((byte)0, byte.MaxValue, byte.MaxValue, byte.MaxValue));
	}

	protected override void OnDrop(DragEventArgs e)
	{
		//IL_003d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0099: Unknown result type (might be due to invalid IL or missing references)
		((UIElement)this).OnDrop(e);
		DragState(over: false);
		if (!e.Data.GetDataPresent(DataFormats.FileDrop))
		{
			return;
		}
		string[] paths = (string[])e.Data.GetData(DataFormats.FileDrop);
		if ((int)((UIElement)ExtView).Visibility == 0)
		{
			ExtInstall(paths);
			return;
		}
		if (cur == null || !cur.Supported)
		{
			Toast((cur == null) ? "Pick a game first" : "This game can't take models yet", ok: false);
			return;
		}
		if (!charsReady)
		{
			Toast("Wait for the characters to load first", ok: false);
			return;
		}
		if ((int)((UIElement)MarketView).Visibility == 0)
		{
			ShowWizard();
		}
		UploadPaths(paths);
	}

	private async Task UploadPaths(IEnumerable<string> paths)
	{
		List<string> list = new List<string>();
		foreach (string path in paths)
		{
			if (Directory.Exists(path))
			{
				list.AddRange(from f in Directory.EnumerateFiles(path, "*", SearchOption.AllDirectories)
					where Wanted.Contains(Path.GetExtension(f))
					select f);
			}
			else if (File.Exists(path))
			{
				list.Add(path);
			}
		}
		if (list.Count == 0)
		{
			Toast("Nothing there looks like a model or texture", ok: false);
			return;
		}
		DropTitle.Text = "Uploading...";
		DropSub.Text = list.Count + " file" + ((list.Count > 1) ? "s" : "");
		DragState(over: true);
		try
		{
			foreach (string item in list)
			{
				foreach (JsonElement item2 in (await api.Put(sid, item)).GetProperty("names").EnumerateArray())
				{
					if (!files.Contains(item2.GetString()))
					{
						files.Add(item2.GetString());
					}
				}
			}
			await FinishLoad();
		}
		catch (Exception ex)
		{
			Toast(Friendly(ex.Message).Item1, ok: false);
			App.Log("upload: " + ex);
			if (!info.HasValue)
			{
				files.Clear();
				sid = NewSid();
			}
			RenderModel();
		}
		finally
		{
			DragState(over: false);
		}
	}

	private async Task FinishLoad()
	{
		info = await api.Post("/api/inspect", new Dictionary<string, object> { { "upload", sid } });
		parts = (from x in info.Value.GetProperty("parts").EnumerateArray()
			select x.GetProperty("i").GetInt32()).ToList();
		ResetEdits();
		if (parts.Count == 0)
		{
			parts.Add(0);
		}
		upAxis = "";
		fwdAxis = "";
		fit = null;
		last = null;
		viewer.Clear();
		ShowPlaceholder(on: true);
		ResetInstallUi();
		RenderModel();
		UpdateSteps();
		Toast("Loaded " + info.Value.GetProperty("file").GetString());
		if (charsReady)
		{
			await RequestFit(first: true);
		}
	}

	private async Task ClearModel()
	{
		try
		{
			await api.Delete("/api/upload?sid=" + sid);
		}
		catch
		{
		}
		sid = NewSid();
		files.Clear();
		info = null;
		fit = null;
		last = null;
		parts = new List<int>();
		ResetEdits();
		viewer.Clear();
		ShowPlaceholder(on: true);
		RenderModel();
		UpdateSteps();
		ResetInstallUi();
	}

	private void RenderModel()
	{
		//IL_030f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0316: Expected O, but got Unknown
		//IL_0128: Unknown result type (might be due to invalid IL or missing references)
		//IL_012f: Unknown result type (might be due to invalid IL or missing references)
		bool hasValue = info.HasValue;
		DropTitle.Text = (hasValue ? "Add more files" : "Drop your model here");
		DropSub.Text = (hasValue ? "textures, or another model" : "a model file + its textures, a folder, or a .zip");
		((UIElement)BtnClearModel).Visibility = (Visibility)((!hasValue) ? 2 : 0);
		HashSet<string> img = new HashSet<string>(StringComparer.OrdinalIgnoreCase) { ".png", ".jpg", ".jpeg", ".tga", ".bmp", ".dds", ".webp", ".tif", ".tiff" };
		FileChips.ItemsSource = files.Select((string f) => new FileChip
		{
			Name = f,
			Tint = (Brush)((!img.Contains(Path.GetExtension(f))) ? ((object)Brushes.White) : ((object)new SolidColorBrush(Color.FromRgb((byte)142, (byte)142, (byte)142))))
		}).ToList();
		((UIElement)AxisPanel).Visibility = (Visibility)((!hasValue) ? 2 : 0);
		Button btnAdv = BtnAdv;
		TextBlock modelSum = ModelSum;
		int num = ((!hasValue) ? 2 : 0);
		Visibility visibility = (Visibility)num;
		((UIElement)modelSum).Visibility = (Visibility)num;
		((UIElement)btnAdv).Visibility = visibility;
		if (!hasValue)
		{
			((UIElement)PartsPanel).Visibility = (Visibility)2;
			((UIElement)AdvPanel).Visibility = (Visibility)2;
			((ContentControl)BtnAdv).Content = "Advanced  +";
			Thumbs.ItemsSource = null;
			return;
		}
		JsonElement value = info.Value;
		int @int = value.GetProperty("textured").GetInt32();
		ModelSum.Text = value.GetProperty("file").GetString() + "  ·  " + value.GetProperty("tris").GetInt32().ToString("N0") + " triangles  ·  " + ((@int == 0) ? "no textures" : (@int + ((@int == 1) ? " texture" : " textures")));
		Anim.Count(StatV, value.GetProperty("verts").GetInt32());
		Anim.Count(StatT, value.GetProperty("tris").GetInt32());
		Anim.Count(StatM, value.GetProperty("materials").GetInt32());
		Anim.Count(StatX, value.GetProperty("textured").GetInt32());
		List<Thumb> list = new List<Thumb>();
		foreach (JsonElement item in value.GetProperty("thumbs").EnumerateArray())
		{
			if (item.ValueKind != JsonValueKind.String)
			{
				list.Add(new Thumb());
				continue;
			}
			try
			{
				BitmapImage val = new BitmapImage();
				val.BeginInit();
				val.CacheOption = (BitmapCacheOption)1;
				val.StreamSource = new MemoryStream(Convert.FromBase64String(item.GetString()));
				val.EndInit();
				((Freezable)val).Freeze();
				list.Add(new Thumb
				{
					Source = (ImageSource)(object)val
				});
			}
			catch
			{
				list.Add(new Thumb());
			}
		}
		Thumbs.ItemsSource = list;
		List<PartRow> list2 = (from p in value.GetProperty("parts").EnumerateArray()
			select new PartRow
			{
				Index = p.GetProperty("i").GetInt32(),
				Name = p.GetProperty("name").GetString(),
				Tris = p.GetProperty("tris").GetInt32().ToString("N0") + " tris",
				On = parts.Contains(p.GetProperty("i").GetInt32())
			}).ToList();
		PartsList.ItemsSource = list2;
		((UIElement)PartsPanel).Visibility = (Visibility)((list2.Count <= 1) ? 2 : 0);
		suppress = true;
		string @string = value.GetProperty("up").GetString();
		string string2 = value.GetProperty("forward").GetString();
		((ItemsControl)UpCombo).ItemsSource = new string[7]
		{
			"Auto (" + @string + ")",
			"+Y",
			"+Z",
			"-Y",
			"-Z",
			"+X",
			"-X"
		};
		((Selector)UpCombo).SelectedIndex = 0;
		((ItemsControl)FwdCombo).ItemsSource = new string[7]
		{
			"Auto (" + string2 + ")",
			"+X",
			"-X",
			"+Y",
			"-Y",
			"+Z",
			"-Z"
		};
		((Selector)FwdCombo).SelectedIndex = 0;
		suppress = false;
	}

	private void OnPartClick(object sender, RoutedEventArgs e)
	{
		if (!(PartsList.ItemsSource is List<PartRow> source))
		{
			return;
		}
		object originalSource = e.OriginalSource;
		CheckBox val = (CheckBox)((originalSource is CheckBox) ? originalSource : null);
		if (val != null && ((FrameworkElement)val).DataContext is PartRow partRow)
		{
			parts = (from p in source
				where p.On
				select p.Index).ToList();
			ResetEdits();
			if (parts.Count == 0)
			{
				partRow.On = true;
				((ToggleButton)val).IsChecked = true;
				parts = new List<int> { partRow.Index };
				Toast("Keep at least one part", ok: false);
			}
			else
			{
				RequestFit(first: false);
			}
		}
	}

	private void BuildSliders()
	{
		//IL_0050: Unknown result type (might be due to invalid IL or missing references)
		//IL_0055: Unknown result type (might be due to invalid IL or missing references)
		//IL_007a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0086: Expected O, but got Unknown
		//IL_008d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0092: Unknown result type (might be due to invalid IL or missing references)
		//IL_0093: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a2: Expected O, but got Unknown
		//IL_00a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_00af: Unknown result type (might be due to invalid IL or missing references)
		//IL_00be: Expected O, but got Unknown
		//IL_00be: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c3: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ca: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ee: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f8: Expected O, but got Unknown
		//IL_00fa: Expected O, but got Unknown
		//IL_00fc: Unknown result type (might be due to invalid IL or missing references)
		//IL_0101: Unknown result type (might be due to invalid IL or missing references)
		//IL_0108: Unknown result type (might be due to invalid IL or missing references)
		//IL_0117: Unknown result type (might be due to invalid IL or missing references)
		//IL_0118: Unknown result type (might be due to invalid IL or missing references)
		//IL_0122: Unknown result type (might be due to invalid IL or missing references)
		//IL_0129: Unknown result type (might be due to invalid IL or missing references)
		//IL_0138: Unknown result type (might be due to invalid IL or missing references)
		//IL_013f: Unknown result type (might be due to invalid IL or missing references)
		//IL_014a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0154: Unknown result type (might be due to invalid IL or missing references)
		//IL_015e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0168: Unknown result type (might be due to invalid IL or missing references)
		//IL_0172: Unknown result type (might be due to invalid IL or missing references)
		//IL_017d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0188: Unknown result type (might be due to invalid IL or missing references)
		//IL_018f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0194: Unknown result type (might be due to invalid IL or missing references)
		//IL_019e: Expected O, but got Unknown
		//IL_019e: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b9: Expected O, but got Unknown
		//IL_01bb: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c0: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c8: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d0: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e5: Unknown result type (might be due to invalid IL or missing references)
		//IL_020c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0224: Unknown result type (might be due to invalid IL or missing references)
		//IL_024b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0252: Unknown result type (might be due to invalid IL or missing references)
		//IL_0277: Unknown result type (might be due to invalid IL or missing references)
		//IL_0281: Unknown result type (might be due to invalid IL or missing references)
		//IL_02aa: Expected O, but got Unknown
		//IL_030d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0317: Expected O, but got Unknown
		//IL_0326: Unknown result type (might be due to invalid IL or missing references)
		//IL_0330: Expected O, but got Unknown
		//IL_033f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0349: Expected O, but got Unknown
		(string, string, double, double, string, double)[] sL = SL;
		for (int i = 0; i < sL.Length; i++)
		{
			(string, string, double, double, string, double) tuple = sL[i];
			string item = tuple.Item1;
			string item2 = tuple.Item2;
			double item3 = tuple.Item3;
			double item4 = tuple.Item4;
			string item5 = tuple.Item5;
			double item6 = tuple.Item6;
			Grid val = new Grid
			{
				Margin = new Thickness(0.0, 0.0, 0.0, 6.0)
			};
			val.RowDefinitions.Add(new RowDefinition
			{
				Height = GridLength.Auto
			});
			val.RowDefinitions.Add(new RowDefinition
			{
				Height = GridLength.Auto
			});
			TextBlock val2 = new TextBlock
			{
				Text = item2,
				FontSize = 12.5,
				Foreground = (Brush)new SolidColorBrush(Color.FromRgb((byte)142, (byte)142, (byte)142))
			};
			TextBox v = new TextBox
			{
				Style = null,
				FontSize = 12.5,
				FontWeight = FontWeights.SemiBold,
				HorizontalAlignment = (HorizontalAlignment)2,
				Width = 72.0,
				TextAlignment = (TextAlignment)1,
				Background = (Brush)(object)Brushes.Transparent,
				BorderThickness = new Thickness(0.0),
				Padding = new Thickness(0.0),
				Foreground = (Brush)(object)Brushes.White,
				CaretBrush = (Brush)(object)Brushes.White,
				SelectionBrush = (Brush)new SolidColorBrush(Color.FromRgb((byte)90, (byte)90, (byte)90)),
				Cursor = Cursors.IBeam,
				ToolTip = "click and type a number (up to 1000)"
			};
			Slider s = new Slider
			{
				Minimum = item3,
				Maximum = item4,
				Value = adj[item] * item6,
				SmallChange = ((item6 == 100.0) ? 1.0 : 0.5),
				LargeChange = ((item6 == 100.0) ? 5 : 5),
				TickFrequency = ((item6 == 100.0) ? 1.0 : 0.5),
				IsSnapToTickEnabled = true,
				Margin = new Thickness(0.0, 3.0, 0.0, 0.0),
				Tag = ((item6 == 100.0) ? ((object)1.0) : null)
			};
			Grid.SetRow((UIElement)(object)s, 1);
			string key = item;
			double mm = item6;
			string uu = item5;
			((RangeBase)s).ValueChanged += delegate(object o, RoutedPropertyChangedEventArgs<double> e)
			{
				if (!suppress)
				{
					ExpandRange(s);
					adj[key] = e.NewValue / mm;
					v.Text = Fmt(adj[key], uu, mm);
					LiveUpdate();
				}
			};
			Action apply = delegate
			{
				if (!double.TryParse(new string(v.Text.Where((char ch) => char.IsDigit(ch) || ch == '.' || ch == '-' || ch == ',').ToArray()).Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out var result) || double.IsNaN(result) || double.IsInfinity(result))
				{
					v.Text = Fmt(adj[key], uu, mm);
				}
				else
				{
					if (mm == 100.0)
					{
						result = Math.Max(1.0, result);
					}
					result = Math.Max(-1000.0, Math.Min(1000.0, result));
					if (result > ((RangeBase)s).Maximum)
					{
						((RangeBase)s).Maximum = Math.Min(1000.0, Math.Ceiling(result * 1.2));
					}
					if (result < ((RangeBase)s).Minimum)
					{
						((RangeBase)s).Minimum = Math.Max(-1000.0, Math.Floor(result - Math.Abs(result) * 0.2 - 1.0));
					}
					suppress = true;
					((RangeBase)s).Value = result;
					suppress = false;
					adj[key] = result / mm;
					v.Text = Fmt(adj[key], uu, mm);
					LiveUpdate();
				}
			};
			((UIElement)v).KeyDown += (KeyEventHandler)delegate(object o, KeyEventArgs e)
			{
				//IL_0001: Unknown result type (might be due to invalid IL or missing references)
				//IL_0007: Invalid comparison between Unknown and I4
				if ((int)e.Key == 6)
				{
					apply();
					Keyboard.ClearFocus();
					((RoutedEventArgs)e).Handled = true;
				}
			};
			((UIElement)v).LostFocus += (RoutedEventHandler)delegate
			{
				apply();
			};
			((UIElement)v).GotKeyboardFocus += (KeyboardFocusChangedEventHandler)delegate
			{
				((TextBoxBase)v).SelectAll();
			};
			((Panel)val).Children.Add((UIElement)(object)val2);
			((Panel)val).Children.Add((UIElement)(object)v);
			((Panel)val).Children.Add((UIElement)(object)s);
			StackPanel obj;
			switch (item)
			{
			default:
				obj = SliderMore;
				break;
			case "scale":
			case "yaw":
			case "pitch":
			case "roll":
				obj = SliderHost;
				break;
			}
			((Panel)obj).Children.Add((UIElement)(object)val);
			sliders[item] = s;
			sliderVals[item] = v;
			v.Text = Fmt(adj[item], item5, item6);
		}
	}

	private static string Fmt(double v, string unit, double mult)
	{
		return ((mult == 100.0) ? Math.Round(v * 100.0).ToString() : (Math.Round(v * 10.0) / 10.0).ToString("0.#")) + unit;
	}

	private void SyncSliders()
	{
		suppress = true;
		(string, string, double, double, string, double)[] sL = SL;
		for (int i = 0; i < sL.Length; i++)
		{
			(string, string, double, double, string, double) tuple = sL[i];
			string item = tuple.Item1;
			double item2 = tuple.Item3;
			double item3 = tuple.Item4;
			string item4 = tuple.Item5;
			double item5 = tuple.Item6;
			double num = adj[item] * item5;
			double num2 = Math.Max(-1000.0, Math.Min(item2, Math.Floor(num - Math.Abs(num) * 0.2 - 1.0)));
			double num3 = Math.Min(1000.0, Math.Max(item3, Math.Ceiling(num * 1.2)));
			((RangeBase)sliders[item]).Minimum = ((Math.Abs(num) <= Math.Abs(item3) && num >= item2) ? item2 : num2);
			((RangeBase)sliders[item]).Maximum = ((num <= item3) ? item3 : num3);
			((RangeBase)sliders[item]).Value = num;
			sliderVals[item].Text = Fmt(adj[item], item4, item5);
		}
		suppress = false;
	}

	private void Rotate(double deg)
	{
		double num = adj["yaw"] + deg;
		num = ((num + 180.0) % 360.0 + 360.0) % 360.0 - 180.0;
		adj["yaw"] = num;
		SyncSliders();
		LiveUpdate();
	}

	private void LiveUpdate()
	{
		if (fit.HasValue && viewer.HasFit)
		{
			Dictionary<string, double> dictionary = last ?? Def();
			viewer.Live(adj["scale"] * adj["width"] / (dictionary["scale"] * dictionary["width"]), adj["scale"] * adj["height"] / (dictionary["scale"] * dictionary["height"]), adj["scale"] * adj["depth"] / (dictionary["scale"] * dictionary["depth"]), adj["yaw"] - dictionary["yaw"], adj["pitch"] - dictionary["pitch"], adj["roll"] - dictionary["roll"], adj["dx"] - dictionary["dx"], adj["dy"] - dictionary["dy"], adj["dz"] - dictionary["dz"]);
		}
		fitTimer.Stop();
		fitTimer.Start();
	}

	private Dictionary<string, object> Payload()
	{
		Dictionary<string, object> dictionary = new Dictionary<string, object>
		{
			{ "game", cur.Id },
			{ "family", fam },
			{ "target", target },
			{ "upload", sid },
			{ "parts", parts },
			{ "up", upAxis },
			{ "forward", fwdAxis }
		};
		foreach (KeyValuePair<string, double> item in adj)
		{
			dictionary[item.Key] = item.Value;
		}
		dictionary["match_pose"] = (matchPose ? 1.0 : 0.0);
		Dictionary<string, object> dictionary2 = EditsJson();
		if (dictionary2 != null)
		{
			dictionary["edits"] = dictionary2;
		}
		return dictionary;
	}

	private async Task RequestFit(bool first)
	{
		if (cur == null || !charsReady || !info.HasValue || parts.Count == 0)
		{
			return;
		}
		int seq = ++fseq;
		SetBusy(on: true, first ? "Rigging your model..." : "Updating...");
		try
		{
			JsonElement jsonElement = await api.Post("/api/fit", Payload());
			if (seq == fseq)
			{
				fit = jsonElement;
				last = new Dictionary<string, double>(adj);
				viewer.SetFit(jsonElement);
				PartsAfterFit(jsonElement);
				if ((int)((UIElement)Placeholder).Visibility == 0)
				{
					ShowPlaceholder(on: false);
				}
				FwdInfo.Text = "faces " + jsonElement.GetProperty("info").GetProperty("forward").GetString();
				BuildTargets(jsonElement);
				if (ModName.Text.Length == 0 && info.HasValue)
				{
					ModName.Text = Path.GetFileNameWithoutExtension(info.Value.GetProperty("file").GetString());
				}
				UpdateSteps();
				if (!installing)
				{
					ResetInstallUi();
				}
			}
		}
		catch (Exception ex)
		{
			if (seq == fseq)
			{
				App.Log("fit: " + ex);
				(string, bool) tuple = Friendly(ex.Message);
				var (text, _) = tuple;
				if (tuple.Item2)
				{
					MarkBroken(cur, text, permanent: true);
				}
				else
				{
					Toast(text, ok: false);
				}
			}
		}
		finally
		{
			if (seq == fseq)
			{
				SetBusy(on: false);
			}
		}
	}

	private void BuildTargets(JsonElement r)
	{
		//IL_00a6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ab: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b5: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bf: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00cb: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d5: Expected O, but got Unknown
		//IL_00d5: Unknown result type (might be due to invalid IL or missing references)
		//IL_00dc: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00eb: Expected O, but got Unknown
		//IL_00eb: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f5: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ff: Unknown result type (might be due to invalid IL or missing references)
		//IL_0109: Unknown result type (might be due to invalid IL or missing references)
		//IL_0114: Expected O, but got Unknown
		//IL_0114: Unknown result type (might be due to invalid IL or missing references)
		//IL_011a: Expected O, but got Unknown
		//IL_013a: Unknown result type (might be due to invalid IL or missing references)
		//IL_013f: Unknown result type (might be due to invalid IL or missing references)
		//IL_014d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0159: Unknown result type (might be due to invalid IL or missing references)
		//IL_0163: Expected O, but got Unknown
		//IL_0163: Unknown result type (might be due to invalid IL or missing references)
		//IL_016e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0185: Expected O, but got Unknown
		//IL_018f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0199: Expected O, but got Unknown
		List<string> list = (from x in r.GetProperty("targets").EnumerateArray()
			select Regex.Replace(x.GetString() ?? "", "^.*SK_NPC_|^.*SK_", "")).ToList();
		if (list.Count < 2)
		{
			((UIElement)TargetBox).Visibility = (Visibility)2;
		}
		else
		{
			if (((Panel)TargetBar).Children.Count == list.Count)
			{
				return;
			}
			((Panel)TargetBar).Children.Clear();
			TargetLabel.Text = "PREVIEW BODY  ·  your settings apply to all " + list.Count;
			Border val = new Border
			{
				CornerRadius = new CornerRadius(10.0),
				Background = (Brush)new SolidColorBrush(Color.FromRgb((byte)13, (byte)13, (byte)13)),
				BorderBrush = (Brush)new SolidColorBrush(Color.FromRgb((byte)34, (byte)34, (byte)34)),
				BorderThickness = new Thickness(1.0),
				Padding = new Thickness(2.0)
			};
			WrapPanel val2 = new WrapPanel();
			for (int i = 0; i < list.Count; i++)
			{
				int idx = i;
				RadioButton val3 = new RadioButton
				{
					Content = list[i],
					Style = (Style)((FrameworkElement)this).FindResource((object)"SegBtn"),
					GroupName = "targets",
					IsChecked = (i == target)
				};
				((ToggleButton)val3).Checked += (RoutedEventHandler)delegate
				{
					if (!suppress && target != idx)
					{
						target = idx;
						last = null;
						RequestFit(first: true);
					}
				};
				((Panel)val2).Children.Add((UIElement)(object)val3);
			}
			((Decorator)val).Child = (UIElement)(object)val2;
			((Panel)TargetBar).Children.Add((UIElement)(object)val);
			((UIElement)TargetBox).Visibility = (Visibility)0;
		}
	}

	private void ResetInstallUi()
	{
		if (!installing)
		{
			((UIElement)StagePanel).Visibility = (Visibility)2;
			((UIElement)LogText).Visibility = (Visibility)2;
			((UIElement)DoneCard).Visibility = (Visibility)((!installed) ? 2 : 0);
			Button btnInstall = BtnInstall;
			bool isEnabled = (((UIElement)BtnSave).IsEnabled = true);
			((UIElement)btnInstall).IsEnabled = isEnabled;
			((ContentControl)BtnInstall).Content = "Install into the game";
		}
	}

	private void SetStage(int n)
	{
		//IL_0063: Unknown result type (might be due to invalid IL or missing references)
		//IL_0068: Unknown result type (might be due to invalid IL or missing references)
		//IL_004d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0040: Unknown result type (might be due to invalid IL or missing references)
		//IL_008a: Unknown result type (might be due to invalid IL or missing references)
		//IL_008f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0094: Unknown result type (might be due to invalid IL or missing references)
		//IL_009a: Expected O, but got Unknown
		//IL_00a4: Unknown result type (might be due to invalid IL or missing references)
		Border[] array = (Border[])(object)new Border[4] { Stage0, Stage1, Stage2, Stage3 };
		for (int i = 0; i < 4; i++)
		{
			Color to = ((i < n) ? Color.FromRgb((byte)244, (byte)244, (byte)244) : ((i == n) ? Color.FromRgb((byte)120, (byte)120, (byte)120) : Color.FromRgb((byte)42, (byte)42, (byte)42)));
			Brush background = array[i].Background;
			SolidColorBrush val = (SolidColorBrush)(object)((background is SolidColorBrush) ? background : null);
			if (val == null || ((Freezable)val).IsFrozen)
			{
				val = new SolidColorBrush(((SolidColorBrush)array[i].Background).Color);
				array[i].Background = (Brush)(object)val;
			}
			Anim.Brush(val, to, 260.0);
		}
	}

	private async Task Install()
	{
		await Install(install: true);
	}

	private async Task Install(bool install)
	{
		if (cur == null || !fit.HasValue || installing)
		{
			return;
		}
		installing = true;
		installed = false;
		((UIElement)DoneCard).Visibility = (Visibility)2;
		Button btnInstall = BtnInstall;
		bool isEnabled = (((UIElement)BtnSave).IsEnabled = false);
		((UIElement)btnInstall).IsEnabled = isEnabled;
		((ContentControl)BtnInstall).Content = "Building...";
		((UIElement)StagePanel).Visibility = (Visibility)0;
		Anim.In((FrameworkElement)(object)StagePanel, 260.0, 6.0);
		((UIElement)LogText).Visibility = (Visibility)0;
		LogText.Text = "starting...";
		int stage = 0;
		SetStage(0);
		Regex[] marks = new Regex[4]
		{
			new Regex("reading|scan|mesh layout|character group", RegexOptions.IgnoreCase),
			new Regex("rigging|autorig|swapped|texture", RegexOptions.IgnoreCase),
			new Regex("pack|built", RegexOptions.IgnoreCase),
			new Regex("install", RegexOptions.IgnoreCase)
		};
		try
		{
			Dictionary<string, object> dictionary = Payload();
			dictionary["name"] = (string.IsNullOrWhiteSpace(ModName.Text) ? "mod" : ModName.Text.Trim());
			dictionary["install"] = install;
			JsonElement jsonElement = await api.Post("/api/apply", dictionary);
			JsonElement jsonElement2 = await api.Job(jsonElement.GetProperty("job").GetString(), delegate(List<string> lines)
			{
				LogText.Text = string.Join("\n", lines.Skip(Math.Max(0, lines.Count - 6)));
				string input = string.Join("\n", lines);
				for (int i = 0; i < marks.Length; i++)
				{
					if (marks[i].IsMatch(input))
					{
						stage = Math.Max(stage, i);
					}
				}
				SetStage(stage);
			});
			SetStage(4);
			lastModId = ((jsonElement2.ValueKind == JsonValueKind.Object && jsonElement2.TryGetProperty("mod", out var value) && value.ValueKind == JsonValueKind.String) ? value.GetString() : "");
			installing = false;
			installed = install;
			((UIElement)LogText).Visibility = (Visibility)2;
			((UIElement)StagePanel).Visibility = (Visibility)2;
			if (install)
			{
				Anim.In((FrameworkElement)(object)DoneCard, 360.0, 10.0);
				Toast("Installed. Launch the game!");
			}
			else
			{
				Toast("Saved to Your mods. Install it any time.");
			}
			LoadMods(cur);
		}
		catch (Exception ex)
		{
			Toast(Friendly(ex.Message).Item1, ok: false);
			App.Log("install: " + ex);
			LogText.Text = ex.Message;
		}
		finally
		{
			installing = false;
			Button btnInstall2 = BtnInstall;
			isEnabled = (((UIElement)BtnSave).IsEnabled = true);
			((UIElement)btnInstall2).IsEnabled = isEnabled;
			((ContentControl)BtnInstall).Content = (installed ? "Install again" : "Install into the game");
			UpdateSteps();
		}
	}

	private async Task Undo()
	{
		if (cur == null)
		{
			return;
		}
		try
		{
			int arrayLength;
			if (!string.IsNullOrEmpty(lastModId))
			{
				JsonElement jsonElement = await api.Post("/api/mod_uninstall", new Dictionary<string, object>
				{
					{ "game", cur.Id },
					{ "id", lastModId }
				});
				arrayLength = (await api.Job(jsonElement.GetProperty("job").GetString(), null)).GetProperty("removed").GetArrayLength();
			}
			else
			{
				arrayLength = (await api.Post("/api/restore", new Dictionary<string, object> { { "game", cur.Id } })).GetProperty("removed").GetArrayLength();
			}
			installed = false;
			lastModId = "";
			Anim.Out_((FrameworkElement)(object)DoneCard, 220.0);
			((ContentControl)BtnInstall).Content = "Install into the game";
			UpdateSteps();
			Toast((arrayLength > 0) ? "Mod removed" : "Nothing to remove");
			LoadMods(cur);
		}
		catch (Exception ex)
		{
			Toast(Friendly(ex.Message).Item1, ok: false);
		}
	}

	private void WireMarketUi()
	{
		//IL_000d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0017: Expected O, but got Unknown
		//IL_0024: Unknown result type (might be due to invalid IL or missing references)
		//IL_002e: Expected O, but got Unknown
		//IL_003b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0045: Expected O, but got Unknown
		//IL_0046: Unknown result type (might be due to invalid IL or missing references)
		//IL_004b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0064: Expected O, but got Unknown
		//IL_0088: Unknown result type (might be due to invalid IL or missing references)
		//IL_0092: Expected O, but got Unknown
		//IL_009f: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a9: Expected O, but got Unknown
		//IL_00b6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c0: Expected O, but got Unknown
		//IL_00cd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d7: Expected O, but got Unknown
		//IL_010e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0118: Expected O, but got Unknown
		//IL_0125: Unknown result type (might be due to invalid IL or missing references)
		//IL_012f: Expected O, but got Unknown
		//IL_013c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0146: Expected O, but got Unknown
		//IL_0158: Unknown result type (might be due to invalid IL or missing references)
		//IL_0162: Expected O, but got Unknown
		//IL_016f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0179: Expected O, but got Unknown
		//IL_00f1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00fc: Expected O, but got Unknown
		((ButtonBase)BtnMarket).Click += (RoutedEventHandler)async delegate
		{
			if (cur != null && cur.Supported)
			{
				modeSuppress = true;
				((ToggleButton)MkLib).IsChecked = true;
				modeSuppress = false;
				SetMarketMode(sf: false);
				ShowMarket();
				await LoadMarket();
			}
		};
		((ToggleButton)MkLib).Checked += (RoutedEventHandler)delegate
		{
			if (!modeSuppress)
			{
				SetMarketMode(sf: false);
				LoadMarket();
			}
		};
		((ToggleButton)MkSf).Checked += (RoutedEventHandler)delegate
		{
			if (!modeSuppress)
			{
				SetMarketMode(sf: true);
				RefreshSf(reset: true);
			}
		};
		sfTimer = new DispatcherTimer
		{
			Interval = TimeSpan.FromMilliseconds(550.0)
		};
		sfTimer.Tick += delegate
		{
			sfTimer.Stop();
			RefreshSf(reset: true);
		};
		((UIElement)MarketSearch).KeyDown += (KeyEventHandler)delegate(object s, KeyEventArgs e)
		{
			//IL_0001: Unknown result type (might be due to invalid IL or missing references)
			//IL_0007: Invalid comparison between Unknown and I4
			if ((int)e.Key == 6 && sfMode)
			{
				sfTimer.Stop();
				RefreshSf(reset: true);
			}
		};
		((TextBoxBase)SfToken).TextChanged += (TextChangedEventHandler)delegate
		{
			((UIElement)SfTokenHint).Visibility = (Visibility)((SfToken.Text.Length != 0) ? 2 : 0);
		};
		((ButtonBase)BtnSfConnect).Click += (RoutedEventHandler)async delegate
		{
			await SfConnectClick(SfToken.Text);
		};
		((ButtonBase)BtnSfOff).Click += (RoutedEventHandler)async delegate
		{
			await SfConnectClick("");
		};
		Button btnSfGet = BtnSfGet;
		object obj = _003C_003Ec._003C_003E9__109_8;
		if (obj == null)
		{
			RoutedEventHandler val = delegate
			{
				OpenUrl("https://sketchfab.com/settings/password");
			};
			_003C_003Ec._003C_003E9__109_8 = val;
			obj = (object)val;
		}
		((ButtonBase)btnSfGet).Click += (RoutedEventHandler)obj;
		((ButtonBase)BtnSfMore).Click += (RoutedEventHandler)async delegate
		{
			await RefreshSf(reset: false);
		};
		((ButtonBase)BtnMarketBack).Click += (RoutedEventHandler)async delegate
		{
			((UIElement)MarketView).Visibility = (Visibility)2;
			if (cur != null)
			{
				await RouteMods(cur);
			}
			else
			{
				ShowWizard();
			}
		};
		((TextBoxBase)MarketSearch).TextChanged += (TextChangedEventHandler)delegate
		{
			((UIElement)MarketSearchHint).Visibility = (Visibility)((MarketSearch.Text.Length != 0) ? 2 : 0);
			if (sfMode)
			{
				sfTimer.Stop();
				sfTimer.Start();
			}
			else
			{
				ApplyMarketFilter();
			}
		};
		((UIElement)MarketList).AddHandler(ButtonBase.ClickEvent, (Delegate)new RoutedEventHandler(OnMarketClick));
		((ButtonBase)BtnMarketFolder).Click += (RoutedEventHandler)async delegate
		{
			try
			{
				await api.Post("/api/market_open");
				Toast("Opened. Drop model folders or .zip files in there.");
			}
			catch (Exception ex)
			{
				Toast(Friendly(ex.Message).Item1, ok: false);
			}
		};
	}

	private void ShowMarket()
	{
		modsMode = false;
		((UIElement)Wizard).Visibility = (Visibility)2;
		((UIElement)ModsView).Visibility = (Visibility)2;
		((UIElement)ExtView).Visibility = (Visibility)2;
		((UIElement)BtnMods).Visibility = (Visibility)2;
		((UIElement)MarketView).Visibility = (Visibility)0;
		Anim.In((FrameworkElement)(object)MarketView, 300.0, 10.0);
	}

	private bool IsForGame(MarketRow r)
	{
		if (cur == null)
		{
			return false;
		}
		string[] games = r.Games;
		foreach (string text in games)
		{
			if (!string.IsNullOrWhiteSpace(text))
			{
				if (string.Equals(text, cur.Id, StringComparison.OrdinalIgnoreCase) || string.Equals(text, cur.AppId, StringComparison.OrdinalIgnoreCase))
				{
					return true;
				}
				if ((cur.Name ?? "").IndexOf(text, StringComparison.OrdinalIgnoreCase) >= 0 || text.IndexOf(cur.Name ?? "\u0001", StringComparison.OrdinalIgnoreCase) >= 0)
				{
					return true;
				}
			}
		}
		return false;
	}

	private static string[] Strs(JsonElement e, string k)
	{
		if (e.TryGetProperty(k, out var value) && value.ValueKind == JsonValueKind.Array)
		{
			return (from x in value.EnumerateArray()
				where x.ValueKind == JsonValueKind.String
				select x.GetString()).ToArray();
		}
		return new string[0];
	}

	private static string Str(JsonElement e, string k)
	{
		if (!e.TryGetProperty(k, out var value) || value.ValueKind != JsonValueKind.String)
		{
			return "";
		}
		return value.GetString();
	}

	private async Task LoadMarket()
	{
		int gen = ++marketGen;
		GameRow g = cur;
		MarketNote.Text = "Loading...";
		((UIElement)MarketEmpty).Visibility = (Visibility)2;
		try
		{
			JsonElement e = await api.Get("/api/market");
			if (gen != marketGen || cur == null || cur != g || sfMode)
			{
				return;
			}
			marketFolder = Str(e, "folder");
			marketBundled = Str(e, "bundled");
			List<MarketRow> list = new List<MarketRow>();
			foreach (JsonElement item in e.GetProperty("models").EnumerateArray())
			{
				JsonElement value;
				JsonElement value2;
				MarketRow marketRow = new MarketRow
				{
					Id = Str(item, "id"),
					Name = Str(item, "name"),
					Author = Str(item, "author"),
					Desc = Str(item, "description"),
					Category = Str(item, "category"),
					TagList = Strs(item, "tags"),
					Games = Strs(item, "games"),
					Size = ((item.TryGetProperty("size", out value) && value.ValueKind == JsonValueKind.Number) ? value.GetInt64() : 0),
					HasPreview = (item.TryGetProperty("preview", out value2) && value2.ValueKind == JsonValueKind.True)
				};
				marketRow.ForThisGame = IsForGame(marketRow);
				list.Add(marketRow);
			}
			marketAll = list;
			List<string> list2 = (from x in e.GetProperty("errors").EnumerateArray()
				select x.GetString()).ToList();
			MarketNote.Text = string.Join("\n", list2);
			((UIElement)MarketNote).Visibility = (Visibility)((list2.Count == 0) ? 2 : 0);
			MarketEmptyText.Text = "Add models and they show up here. Put a folder (the model file + its textures) or a .zip for each model into either of these folders:\n\n•  " + marketBundled + "\n•  " + marketFolder + "\n\nThe folder or file name is the name shown here. Optional: put a preview.png in the folder for a picture, and an info.json for author, tags and which game it's for.";
			BuildMarketChips();
			ApplyMarketFilter();
			LoadMarketPreviews(list, gen);
		}
		catch (Exception ex)
		{
			MarketNote.Text = Friendly(ex.Message).Item1;
			((UIElement)MarketNote).Visibility = (Visibility)0;
			App.Log("market: " + ex);
		}
	}

	private void BuildMarketChips()
	{
		//IL_019b: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a0: Unknown result type (might be due to invalid IL or missing references)
		//IL_01ac: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b6: Expected O, but got Unknown
		//IL_01b6: Unknown result type (might be due to invalid IL or missing references)
		//IL_01be: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c9: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d1: Unknown result type (might be due to invalid IL or missing references)
		//IL_01eb: Expected O, but got Unknown
		//IL_01f4: Unknown result type (might be due to invalid IL or missing references)
		//IL_01fe: Expected O, but got Unknown
		((Panel)MarketChips).Children.Clear();
		List<(string, string)> list = new List<(string, string)> { ("all", "All") };
		if (marketAll.Any((MarketRow r) => r.ForThisGame))
		{
			list.Add(("@game", "This game"));
		}
		foreach (string item3 in from c in (from r in marketAll
				select r.Category into c
				where !string.IsNullOrEmpty(c)
				select c).Distinct()
			orderby c
			select c)
		{
			char reference = char.ToUpperInvariant(item3[0]);
			list.Add((item3, string.Concat(new ReadOnlySpan<char>(ref reference), item3.Substring(1))));
		}
		if (!list.Any<(string, string)>(((string key, string label) c) => c.key == marketCat))
		{
			marketCat = "all";
		}
		if (list.Count <= 1)
		{
			((UIElement)MarketChips).Visibility = (Visibility)2;
			return;
		}
		((UIElement)MarketChips).Visibility = (Visibility)0;
		foreach (var item4 in list)
		{
			string item = item4.Item1;
			string item2 = item4.Item2;
			RadioButton val = new RadioButton
			{
				Style = (Style)((FrameworkElement)this).FindResource((object)"SegBtn"),
				Content = item2,
				GroupName = "mk",
				Tag = item,
				IsChecked = (item == marketCat)
			};
			((ToggleButton)val).Checked += (RoutedEventHandler)delegate(object s, RoutedEventArgs e)
			{
				//IL_0002: Unknown result type (might be due to invalid IL or missing references)
				marketCat = (string)((FrameworkElement)(RadioButton)s).Tag;
				ApplyMarketFilter();
			};
			((Panel)MarketChips).Children.Add((UIElement)(object)val);
		}
	}

	private void ApplyMarketFilter()
	{
		if (sfMode)
		{
			return;
		}
		string[] toks = (MarketSearch.Text ?? "").ToLowerInvariant().Split(new char[1] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
		IEnumerable<MarketRow> source = marketAll;
		if (marketCat == "@game")
		{
			source = source.Where((MarketRow r) => r.ForThisGame);
		}
		else if (marketCat != "all")
		{
			source = source.Where((MarketRow r) => r.Category == marketCat);
		}
		if (toks.Length != 0)
		{
			source = source.Where(delegate(MarketRow r)
			{
				string hay = (r.Name + " " + r.Author + " " + r.Category + " " + string.Join(" ", r.TagList) + " " + r.Desc).ToLowerInvariant();
				return toks.All((string t) => hay.Contains(t));
			});
		}
		List<MarketRow> list = source.OrderByDescending((MarketRow r) => r.ForThisGame).ThenBy<MarketRow, string>((MarketRow r) => r.Name, StringComparer.OrdinalIgnoreCase).ToList();
		MarketList.ItemsSource = list;
		((UIElement)MarketEmpty).Visibility = (Visibility)((marketAll.Count != 0) ? 2 : 0);
		if (marketAll.Count > 0 && list.Count == 0)
		{
			MarketNote.Text = "No models match that.";
			((UIElement)MarketNote).Visibility = (Visibility)0;
		}
		else if (MarketNote.Text == "No models match that." || MarketNote.Text == "Loading...")
		{
			((UIElement)MarketNote).Visibility = (Visibility)2;
		}
	}

	private async Task LoadMarketPreviews(List<MarketRow> rows, int gen, bool sf = false)
	{
		SemaphoreSlim gate = new SemaphoreSlim(4);
		await Task.WhenAll(rows.Where((MarketRow r) => r.HasPreview).Select((Func<MarketRow, Task>)async delegate(MarketRow r)
		{
			await gate.WaitAsync();
			try
			{
				if (!((!sf) ? (gen != marketGen) : (!sfMode || gen != int.MinValue + sfGen)))
				{
					byte[] array = await api.GetBytes("/api/market_preview?id=" + Uri.EscapeDataString(r.Id));
					if (array != null && !((!sf) ? (gen != marketGen) : (!sfMode || gen != int.MinValue + sfGen)))
					{
						BitmapImage val = new BitmapImage();
						val.BeginInit();
						val.CacheOption = (BitmapCacheOption)1;
						val.StreamSource = new MemoryStream(array);
						val.EndInit();
						((Freezable)val).Freeze();
						r.Preview = (ImageSource)(object)val;
					}
				}
			}
			catch (Exception ex)
			{
				App.Log("market preview: " + ex.Message);
			}
			finally
			{
				gate.Release();
			}
		}).ToList());
	}

	private async void OnMarketClick(object sender, RoutedEventArgs e)
	{
		object originalSource = e.OriginalSource;
		Button val = (Button)((originalSource is Button) ? originalSource : null);
		if (val != null && ((FrameworkElement)val).DataContext is MarketRow marketRow)
		{
			if (((FrameworkElement)val).Tag as string == "page")
			{
				OpenUrl(marketRow.Url);
			}
			else if (!(((FrameworkElement)val).Tag as string != "use"))
			{
				await UseMarketModel(marketRow);
			}
		}
	}

	private async Task UseMarketModel(MarketRow row)
	{
		if (cur == null || !cur.Supported || marketBusy)
		{
			return;
		}
		if (row.IsSketchfab && !sfConnected)
		{
			Toast("Connect Sketchfab first: paste your API token above (one time)", ok: false);
			((UIElement)SfToken).Focus();
			return;
		}
		marketBusy = true;
		((UIElement)MarketList).IsEnabled = false;
		MarketNote.Text = "Getting " + row.Name + "...";
		((UIElement)MarketNote).Visibility = (Visibility)0;
		try
		{
			await ClearModel();
			JsonElement jsonElement = await api.Post("/api/market_get", new Dictionary<string, object>
			{
				{ "id", row.Id },
				{ "upload", sid }
			});
			JsonElement jsonElement2 = await api.Job(jsonElement.GetProperty("job").GetString(), delegate(List<string> lines)
			{
				if (lines.Count > 0)
				{
					MarketNote.Text = row.Name + ": " + lines[lines.Count - 1];
				}
			});
			files.Clear();
			foreach (JsonElement item in jsonElement2.GetProperty("names").EnumerateArray())
			{
				files.Add(item.GetString());
			}
			((UIElement)MarketView).Visibility = (Visibility)2;
			ShowWizard();
			try
			{
				await FinishLoad();
			}
			catch (Exception ex)
			{
				Toast(Friendly(ex.Message).Item1, ok: false);
				App.Log("market load: " + ex);
				await ClearModel();
			}
			if (info.HasValue)
			{
				Toast(row.Name + " is ready. Pick the character it replaces, then press Install.");
				if (row.IsSketchfab)
				{
					bool flag = !string.IsNullOrEmpty(row.License) && (row.License.IndexOf("NonCommercial", StringComparison.OrdinalIgnoreCase) >= 0 || row.License.IndexOf("-NC", StringComparison.OrdinalIgnoreCase) >= 0 || row.License.IndexOf(" NC", StringComparison.OrdinalIgnoreCase) >= 0);
					Toast("By " + row.Author + "  ·  " + (string.IsNullOrEmpty(row.License) ? "check the licence on its page" : row.License) + (flag ? "  ·  not for selling" : "") + ". Credit saved to sketchfab_credits.txt.");
				}
			}
		}
		catch (Exception ex2)
		{
			MarketNote.Text = Friendly(ex2.Message).Item1;
			Toast(Friendly(ex2.Message).Item1, ok: false);
			App.Log("market get: " + ex2);
		}
		finally
		{
			marketBusy = false;
			((UIElement)MarketList).IsEnabled = true;
		}
	}

	private static void OpenUrl(string url)
	{
		if (string.IsNullOrEmpty(url) || !url.StartsWith("https://"))
		{
			return;
		}
		try
		{
			Process.Start(new ProcessStartInfo(url)
			{
				UseShellExecute = true
			});
		}
		catch
		{
		}
	}

	private void SetMarketMode(bool sf)
	{
		sfMode = sf;
		MarketSearch.Text = "";
		sfRows.Clear();
		sfCursor = "";
		marketGen++;
		sfGen++;
		MarketIntro.Text = (sf ? "Search Sketchfab's downloadable models. Searching is free; to use one, connect your Sketchfab account once. Every model keeps its author's licence, shown on the card." : "Pick a model and ModSwap loads it for you. Then choose which character it replaces and press Install. No need to go to a model site.");
		MarketSearchHint.Text = (sf ? "Search Sketchfab (goku, police car, sword...)" : "Search models");
		((UIElement)SfConnect).Visibility = (Visibility)((!sf) ? 2 : 0);
		((UIElement)BtnMarketFolder).Visibility = (Visibility)(sf ? 2 : 0);
		((UIElement)BtnSfMore).Visibility = (Visibility)2;
		((UIElement)MarketEmpty).Visibility = (Visibility)2;
		MarketList.ItemsSource = null;
		MarketNote.Text = "";
		if (sf)
		{
			BuildSfChips();
		}
		UpdateSfPanel();
	}

	private void BuildSfChips()
	{
		//IL_00ac: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c7: Expected O, but got Unknown
		//IL_00c7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ce: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f9: Expected O, but got Unknown
		//IL_0102: Unknown result type (might be due to invalid IL or missing references)
		//IL_010c: Expected O, but got Unknown
		((Panel)MarketChips).Children.Clear();
		((UIElement)MarketChips).Visibility = (Visibility)0;
		(string, string)[] array = new(string, string)[5]
		{
			("popular", "Popular"),
			("newest", "Newest"),
			("characters", "Characters"),
			("vehicles", "Vehicles"),
			("weapons", "Weapons")
		};
		for (int i = 0; i < array.Length; i++)
		{
			(string, string) tuple = array[i];
			string item = tuple.Item1;
			string item2 = tuple.Item2;
			RadioButton val = new RadioButton
			{
				Style = (Style)((FrameworkElement)this).FindResource((object)"SegBtn"),
				Content = item2,
				GroupName = "mksf",
				Tag = item,
				IsChecked = (item == sfCur)
			};
			((ToggleButton)val).Checked += (RoutedEventHandler)delegate(object s, RoutedEventArgs e)
			{
				//IL_0002: Unknown result type (might be due to invalid IL or missing references)
				sfCur = (string)((FrameworkElement)(RadioButton)s).Tag;
				RefreshSf(reset: true);
			};
			((Panel)MarketChips).Children.Add((UIElement)(object)val);
		}
	}

	private void UpdateSfPanel()
	{
		SfTitle.Text = (sfConnected ? ("Connected to Sketchfab" + (string.IsNullOrEmpty(sfUser) ? "" : (" as " + sfUser))) : "Connect Sketchfab to download");
		SfText.Text = (sfConnected ? "You can use any model here. Your token stays on this PC and is only sent to Sketchfab." : "Sketchfab only lets signed-in people download. Press Get my token, copy the \"API token\" from that page, paste it here and press Connect. You only do this once, and it stays on this PC.");
		((UIElement)SfTokenRow).Visibility = (Visibility)(sfConnected ? 2 : 0);
		((UIElement)BtnSfOff).Visibility = (Visibility)((!sfConnected) ? 2 : 0);
	}

	private async Task SfConnectClick(string token)
	{
		try
		{
			JsonElement e = await api.Post("/api/sketchfab_connect", new Dictionary<string, object> { 
			{
				"token",
				token ?? ""
			} });
			sfConnected = e.GetProperty("connected").GetBoolean();
			sfUser = Str(e, "user");
			SfToken.Text = "";
			UpdateSfPanel();
			Toast(sfConnected ? ("Connected to Sketchfab" + ((sfUser.Length > 0) ? (" as " + sfUser) : "")) : "Disconnected from Sketchfab");
		}
		catch (Exception ex)
		{
			Toast(Friendly(ex.Message).Item1, ok: false);
			App.Log("sketchfab connect: " + ex.Message);
		}
	}

	private async Task RefreshSf(bool reset)
	{
		int gen = ++sfGen;
		GameRow g = cur;
		if (reset)
		{
			sfCursor = "";
			sfRows.Clear();
			((UIElement)BtnSfMore).Visibility = (Visibility)2;
		}
		string text = (MarketSearch.Text ?? "").Trim();
		string text2 = "popular";
		string text3 = "";
		if (sfCur == "newest")
		{
			text2 = "newest";
		}
		else
		{
			if (sfCur != "popular")
			{
				text3 = sfCur;
			}
			if (text.Length > 0)
			{
				text2 = "relevant";
			}
		}
		MarketNote.Text = "Searching Sketchfab...";
		((UIElement)MarketNote).Visibility = (Visibility)0;
		try
		{
			JsonElement e = await api.Get("/api/sketchfab?q=" + Uri.EscapeDataString(text) + "&sort=" + text2 + "&cat=" + text3 + "&cursor=" + Uri.EscapeDataString(sfCursor));
			if (gen != sfGen || !sfMode || cur != g)
			{
				return;
			}
			sfConnected = e.GetProperty("connected").GetBoolean();
			sfUser = Str(e, "user");
			UpdateSfPanel();
			List<MarketRow> list = new List<MarketRow>();
			foreach (JsonElement item in e.GetProperty("models").EnumerateArray())
			{
				JsonElement value;
				int num = ((item.TryGetProperty("faces", out value) && value.ValueKind == JsonValueKind.Number) ? value.GetInt32() : 0);
				string text4 = Str(item, "license");
				List<string> list2 = new List<string>();
				if (text4.Length > 0)
				{
					list2.Add(text4);
				}
				if (num > 0)
				{
					list2.Add(((num >= 1000) ? (((double)num / 1000.0).ToString("0.#") + "k") : num.ToString()) + " faces");
				}
				list.Add(new MarketRow
				{
					Id = Str(item, "id"),
					Name = Str(item, "name"),
					Author = Str(item, "author"),
					License = text4,
					Url = Str(item, "url"),
					HasPreview = true,
					TagsText = string.Join("  ·  ", list2)
				});
			}
			sfRows.AddRange(list);
			sfCursor = Str(e, "next");
			MarketList.ItemsSource = null;
			MarketList.ItemsSource = new List<MarketRow>(sfRows);
			((UIElement)BtnSfMore).Visibility = (Visibility)((sfCursor.Length <= 0) ? 2 : 0);
			MarketNote.Text = ((sfRows.Count == 0) ? "Nothing found. Try another word." : "");
			((UIElement)MarketNote).Visibility = (Visibility)((sfRows.Count != 0) ? 2 : 0);
			LoadMarketPreviews(list, int.MinValue + gen, sf: true);
		}
		catch (Exception ex)
		{
			if (gen == sfGen)
			{
				MarketNote.Text = Friendly(ex.Message).Item1;
				((UIElement)MarketNote).Visibility = (Visibility)0;
			}
			App.Log("sketchfab: " + ex.Message);
		}
	}

	private void ExpandRange(Slider s)
	{
		if (unlimited)
		{
			double num = ((RangeBase)s).Maximum - ((RangeBase)s).Minimum;
			if (((RangeBase)s).Value >= ((RangeBase)s).Maximum - num * 0.05)
			{
				((RangeBase)s).Maximum = Math.Min(1000.0, ((RangeBase)s).Maximum + num * 0.6);
			}
			double num3 = ((((FrameworkElement)s).Tag is double num2) ? num2 : (-1000.0));
			if (((RangeBase)s).Value <= ((RangeBase)s).Minimum + num * 0.05 && ((RangeBase)s).Minimum > num3)
			{
				((RangeBase)s).Minimum = Math.Max(Math.Max(num3, -1000.0), ((RangeBase)s).Minimum - num * 0.6);
			}
		}
	}

	private void SetUnlimited(bool on)
	{
		unlimited = on;
		if (!on)
		{
			suppress = true;
			(string, string, double, double, string, double)[] sL = SL;
			for (int i = 0; i < sL.Length; i++)
			{
				(string, string, double, double, string, double) tuple = sL[i];
				string item = tuple.Item1;
				double item2 = tuple.Item3;
				double item3 = tuple.Item4;
				string item4 = tuple.Item5;
				double item5 = tuple.Item6;
				Slider obj = sliders[item];
				((RangeBase)obj).Minimum = item2;
				((RangeBase)obj).Maximum = item3;
				double num = Math.Max(item2, Math.Min(item3, adj[item] * item5));
				adj[item] = num / item5;
				((RangeBase)obj).Value = num;
				sliderVals[item].Text = Fmt(adj[item], item4, item5);
			}
			suppress = false;
			LiveUpdate();
		}
	}

	private PartOp OpOf(int id)
	{
		if (id >= 100)
		{
			return customs[id - 100].Op;
		}
		if (!autoOps.TryGetValue(id, out var value))
		{
			value = (autoOps[id] = new PartOp());
		}
		return value;
	}

	private PartOp SelOp()
	{
		if (selPart >= 0)
		{
			return OpOf(selPart);
		}
		return null;
	}

	private void ResetEdits()
	{
		autoOps.Clear();
		customs.Clear();
		selPart = -1;
		vgroup = null;
		vertN = 0;
		if (partsBuilt)
		{
			RebuildChips();
			((UIElement)PartOps).Visibility = (Visibility)2;
		}
		viewer.SetHighlight(null);
		SetTool("");
		ClearToolCanvas();
	}

	private Dictionary<string, object> EditsJson()
	{
		Dictionary<string, object> dictionary = new Dictionary<string, object>();
		foreach (KeyValuePair<int, PartOp> autoOp in autoOps)
		{
			if (!autoOp.Value.IsDefault)
			{
				dictionary[autoOp.Key.ToString()] = autoOp.Value.ToJson();
			}
		}
		List<object> list = new List<object>();
		foreach (CustomPart custom in customs)
		{
			if (!custom.Op.IsDefault)
			{
				Dictionary<string, object> dictionary2 = custom.Op.ToJson();
				dictionary2["mask"] = Convert.ToBase64String(PackBits(custom.Mask));
				list.Add(dictionary2);
			}
		}
		if (dictionary.Count == 0 && list.Count == 0)
		{
			return null;
		}
		return new Dictionary<string, object>
		{
			{ "g", dictionary },
			{ "c", list }
		};
	}

	private static byte[] PackBits(bool[] m)
	{
		byte[] array = new byte[(m.Length + 7) / 8];
		for (int i = 0; i < m.Length; i++)
		{
			if (m[i])
			{
				array[i >> 3] |= (byte)(128 >> (i & 7));
			}
		}
		return array;
	}

	private void PartsAfterFit(JsonElement r)
	{
		JsonElement value;
		bool flag = r.TryGetProperty("static", out value) && value.ValueKind == JsonValueKind.True;
		((UIElement)BtnPartsEdit).Visibility = (Visibility)(flag ? 2 : 0);
		if (flag)
		{
			((UIElement)PartsEditor).Visibility = (Visibility)2;
			SetTool("");
			viewer.SetHighlight(null);
			return;
		}
		try
		{
			JsonElement property = r.GetProperty("groups");
			vgroup = Convert.FromBase64String(property.GetProperty("ids").GetString());
			groupNames = (from x in property.GetProperty("names").EnumerateArray()
				select x.GetString()).ToArray();
			vertN = r.GetProperty("new").GetProperty("n").GetInt32();
		}
		catch
		{
		}
		if (!partsBuilt)
		{
			BuildPartsUi();
		}
		RefreshHighlight();
	}

	private void RebuildChips()
	{
		suppress = true;
		((Panel)PartChips).Children.Clear();
		for (int i = 0; i < 6; i++)
		{
			AddChip(i, groupNames[i]);
		}
		for (int j = 0; j < customs.Count; j++)
		{
			AddChip(100 + j, customs[j].Name);
		}
		suppress = false;
	}

	private void AddChip(int id, string text)
	{
		//IL_0000: Unknown result type (might be due to invalid IL or missing references)
		//IL_0005: Unknown result type (might be due to invalid IL or missing references)
		//IL_0011: Unknown result type (might be due to invalid IL or missing references)
		//IL_001b: Expected O, but got Unknown
		//IL_001b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0022: Unknown result type (might be due to invalid IL or missing references)
		//IL_002d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0039: Unknown result type (might be due to invalid IL or missing references)
		//IL_005e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0068: Unknown result type (might be due to invalid IL or missing references)
		//IL_007d: Expected O, but got Unknown
		//IL_0085: Unknown result type (might be due to invalid IL or missing references)
		//IL_008f: Expected O, but got Unknown
		RadioButton val = new RadioButton
		{
			Style = (Style)((FrameworkElement)this).FindResource((object)"SegBtn"),
			Content = text,
			GroupName = "partsel",
			Tag = id,
			Margin = new Thickness(0.0, 0.0, 4.0, 4.0),
			IsChecked = (id == selPart)
		};
		((ToggleButton)val).Checked += (RoutedEventHandler)delegate(object s, RoutedEventArgs e)
		{
			//IL_000b: Unknown result type (might be due to invalid IL or missing references)
			if (!suppress)
			{
				selPart = (int)((FrameworkElement)(RadioButton)s).Tag;
				ShowPartOps();
			}
		};
		((Panel)PartChips).Children.Add((UIElement)(object)val);
	}

	private void BuildPartsUi()
	{
		//IL_0195: Unknown result type (might be due to invalid IL or missing references)
		//IL_019a: Unknown result type (might be due to invalid IL or missing references)
		//IL_01bf: Unknown result type (might be due to invalid IL or missing references)
		//IL_01cb: Expected O, but got Unknown
		//IL_01d2: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d7: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d8: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e7: Expected O, but got Unknown
		//IL_01ee: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f3: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f4: Unknown result type (might be due to invalid IL or missing references)
		//IL_0203: Expected O, but got Unknown
		//IL_0203: Unknown result type (might be due to invalid IL or missing references)
		//IL_0208: Unknown result type (might be due to invalid IL or missing references)
		//IL_0214: Unknown result type (might be due to invalid IL or missing references)
		//IL_0223: Unknown result type (might be due to invalid IL or missing references)
		//IL_0233: Unknown result type (might be due to invalid IL or missing references)
		//IL_0238: Unknown result type (might be due to invalid IL or missing references)
		//IL_0242: Expected O, but got Unknown
		//IL_0244: Expected O, but got Unknown
		//IL_0250: Unknown result type (might be due to invalid IL or missing references)
		//IL_0255: Unknown result type (might be due to invalid IL or missing references)
		//IL_0261: Unknown result type (might be due to invalid IL or missing references)
		//IL_026d: Unknown result type (might be due to invalid IL or missing references)
		//IL_027c: Unknown result type (might be due to invalid IL or missing references)
		//IL_028b: Unknown result type (might be due to invalid IL or missing references)
		//IL_02b0: Unknown result type (might be due to invalid IL or missing references)
		//IL_02ba: Unknown result type (might be due to invalid IL or missing references)
		//IL_02e7: Expected O, but got Unknown
		//IL_0397: Unknown result type (might be due to invalid IL or missing references)
		//IL_03a1: Expected O, but got Unknown
		//IL_03ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_03b8: Expected O, but got Unknown
		//IL_03c5: Unknown result type (might be due to invalid IL or missing references)
		//IL_03cf: Expected O, but got Unknown
		partsBuilt = true;
		RebuildChips();
		(string, double, double, string, double, int, int)[] array = new(string, double, double, string, double, int, int)[7]
		{
			("Move left / right", -60.0, 60.0, " cm", 1.0, 0, 0),
			("Move forward / back", -60.0, 60.0, " cm", 1.0, 0, 1),
			("Move up / down", -60.0, 60.0, " cm", 1.0, 0, 2),
			("Size", 20.0, 300.0, "%", 100.0, 1, 0),
			("Tilt forward / back", -90.0, 90.0, "°", 1.0, 2, 0),
			("Turn", -180.0, 180.0, "°", 1.0, 2, 1),
			("Lean left / right", -90.0, 90.0, "°", 1.0, 2, 2)
		};
		for (int i = 0; i < array.Length; i++)
		{
			(string, double, double, string, double, int, int) tuple = array[i];
			Grid val2 = new Grid
			{
				Margin = new Thickness(0.0, 0.0, 0.0, 6.0)
			};
			val2.RowDefinitions.Add(new RowDefinition
			{
				Height = GridLength.Auto
			});
			val2.RowDefinitions.Add(new RowDefinition
			{
				Height = GridLength.Auto
			});
			TextBlock val3 = new TextBlock
			{
				Text = tuple.Item1,
				FontSize = 12.5,
				Foreground = (Brush)new SolidColorBrush(Color.FromRgb((byte)142, (byte)142, (byte)142))
			};
			TextBox v = MakeValueBox();
			Slider s = new Slider
			{
				Minimum = tuple.Item2,
				Maximum = tuple.Item3,
				SmallChange = 1.0,
				LargeChange = 5.0,
				Margin = new Thickness(0.0, 3.0, 0.0, 0.0),
				Tag = ((tuple.Item5 == 100.0) ? ((object)1.0) : null)
			};
			Grid.SetRow((UIElement)(object)s, 1);
			((Panel)val2).Children.Add((UIElement)(object)val3);
			((Panel)val2).Children.Add((UIElement)(object)v);
			((Panel)val2).Children.Add((UIElement)(object)s);
			((Panel)PartSliders).Children.Add((UIElement)(object)val2);
			partSliderList.Add(s);
			(string label, double min, double max, string unit, double mult, int kind, int idx) spec = tuple;
			Func<PartOp, double> @object = (PartOp o) => (spec.kind != 0) ? ((spec.kind != 1) ? o.Rot[spec.idx] : (o.Scale * 100.0)) : o.Move[spec.idx];
			Action<PartOp, double> set = delegate(PartOp o, double val)
			{
				if (spec.kind == 0)
				{
					o.Move[spec.idx] = val;
				}
				else if (spec.kind == 1)
				{
					o.Scale = Math.Max(0.01, val / 100.0);
				}
				else
				{
					o.Rot[spec.idx] = val;
				}
			};
			((RangeBase)s).ValueChanged += delegate(object o2, RoutedPropertyChangedEventArgs<double> e2)
			{
				if (!suppress)
				{
					PartOp partOp = SelOp();
					if (partOp != null)
					{
						ExpandRange(s);
						set(partOp, e2.NewValue);
						v.Text = Math.Round(e2.NewValue, 1).ToString("0.#") + spec.unit;
						QueueEditRefit();
					}
				}
			};
			((UIElement)v).KeyDown += (KeyEventHandler)delegate(object o2, KeyEventArgs e2)
			{
				//IL_0001: Unknown result type (might be due to invalid IL or missing references)
				//IL_0007: Invalid comparison between Unknown and I4
				if ((int)e2.Key == 6)
				{
					CommitBox(v, s, spec.unit, (spec.mult == 100.0) ? 1.0 : double.NegativeInfinity);
					Keyboard.ClearFocus();
					((RoutedEventArgs)e2).Handled = true;
				}
			};
			((UIElement)v).LostFocus += (RoutedEventHandler)delegate
			{
				CommitBox(v, s, spec.unit, (spec.mult == 100.0) ? 1.0 : double.NegativeInfinity);
			};
			((UIElement)v).GotKeyboardFocus += (KeyboardFocusChangedEventHandler)delegate
			{
				((TextBoxBase)v).SelectAll();
			};
			((FrameworkElement)v).Tag = new Func<PartOp, double>(@object.Invoke);
		}
	}

	private static TextBox MakeValueBox()
	{
		//IL_0000: Unknown result type (might be due to invalid IL or missing references)
		//IL_0005: Unknown result type (might be due to invalid IL or missing references)
		//IL_000c: Unknown result type (might be due to invalid IL or missing references)
		//IL_001b: Unknown result type (might be due to invalid IL or missing references)
		//IL_001c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0026: Unknown result type (might be due to invalid IL or missing references)
		//IL_002d: Unknown result type (might be due to invalid IL or missing references)
		//IL_003c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0043: Unknown result type (might be due to invalid IL or missing references)
		//IL_004e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0058: Unknown result type (might be due to invalid IL or missing references)
		//IL_0062: Unknown result type (might be due to invalid IL or missing references)
		//IL_006c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0076: Unknown result type (might be due to invalid IL or missing references)
		//IL_0081: Unknown result type (might be due to invalid IL or missing references)
		//IL_008c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0093: Unknown result type (might be due to invalid IL or missing references)
		//IL_0098: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a2: Expected O, but got Unknown
		//IL_00a2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ad: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b9: Expected O, but got Unknown
		return new TextBox
		{
			Style = null,
			FontSize = 12.5,
			FontWeight = FontWeights.SemiBold,
			HorizontalAlignment = (HorizontalAlignment)2,
			Width = 72.0,
			TextAlignment = (TextAlignment)1,
			Background = (Brush)(object)Brushes.Transparent,
			BorderThickness = new Thickness(0.0),
			Padding = new Thickness(0.0),
			Foreground = (Brush)(object)Brushes.White,
			CaretBrush = (Brush)(object)Brushes.White,
			SelectionBrush = (Brush)new SolidColorBrush(Color.FromRgb((byte)90, (byte)90, (byte)90)),
			Cursor = Cursors.IBeam,
			ToolTip = "click and type any number, there's no limit"
		};
	}

	private void CommitBox(TextBox v, Slider s, string unit, double floor)
	{
		if (!double.TryParse(new string(v.Text.Where((char ch) => char.IsDigit(ch) || ch == '.' || ch == '-' || ch == ',').ToArray()).Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out var result) || double.IsNaN(result) || double.IsInfinity(result))
		{
			v.Text = Math.Round(((RangeBase)s).Value, 1).ToString("0.#") + unit;
			return;
		}
		result = Math.Max(floor, Math.Max(-1000.0, Math.Min(1000.0, result)));
		if (result > ((RangeBase)s).Maximum)
		{
			((RangeBase)s).Maximum = Math.Min(1000.0, Math.Ceiling(result * 1.2));
		}
		if (result < ((RangeBase)s).Minimum)
		{
			((RangeBase)s).Minimum = Math.Max(-1000.0, Math.Floor(result - Math.Abs(result) * 0.2 - 1.0));
		}
		((RangeBase)s).Value = result;
		v.Text = Math.Round(result, 1).ToString("0.#") + unit;
	}

	private void ShowPartOps()
	{
		//IL_01af: Unknown result type (might be due to invalid IL or missing references)
		PartOp partOp = SelOp();
		if (partOp == null)
		{
			((UIElement)PartOps).Visibility = (Visibility)2;
			return;
		}
		suppress = true;
		((ToggleButton)ChkHide).IsChecked = partOp.Hide;
		int num = 0;
		foreach (Grid item in ((IEnumerable)((Panel)PartSliders).Children).OfType<Grid>())
		{
			Slider val = partSliderList[num++];
			TextBox obj = ((IEnumerable)((Panel)item).Children).OfType<TextBox>().First();
			double num2 = ((Func<PartOp, double>)((FrameworkElement)obj).Tag)(partOp);
			if (num2 > ((RangeBase)val).Maximum)
			{
				((RangeBase)val).Maximum = Math.Min(1000.0, Math.Ceiling(num2 * 1.2));
			}
			if (num2 < ((RangeBase)val).Minimum)
			{
				((RangeBase)val).Minimum = Math.Max(-1000.0, Math.Floor(num2 - Math.Abs(num2) * 0.2 - 1.0));
			}
			((RangeBase)val).Value = num2;
			obj.Text = string.Concat(str1: (num == 4) ? "%" : ((num <= 3) ? " cm" : "°"), str0: Math.Round(num2, 1).ToString("0.#"));
		}
		suppress = false;
		bool flag = selPart >= 2 && selPart <= 5;
		((UIElement)BtnPartMirror).Visibility = (Visibility)((!flag) ? 2 : 0);
		((UIElement)BtnPartRemove).Visibility = (Visibility)((selPart < 100) ? 2 : 0);
		if ((int)((UIElement)PartOps).Visibility != 0)
		{
			((UIElement)PartOps).Visibility = (Visibility)0;
			Anim.In((FrameworkElement)(object)PartOps, 260.0, 8.0);
		}
		RefreshHighlight();
	}

	private void QueueEditRefit()
	{
		fitTimer.Stop();
		fitTimer.Start();
	}

	private void RefreshHighlight()
	{
		if (selPart < 0 || vertN == 0)
		{
			viewer.SetHighlight(null);
			return;
		}
		bool[] highlight = SelMask();
		viewer.SetHighlight(highlight);
	}

	private bool[] SelMask()
	{
		if (selPart >= 100)
		{
			if (selPart - 100 >= customs.Count)
			{
				return null;
			}
			return customs[selPart - 100].Mask;
		}
		if (vgroup == null)
		{
			return null;
		}
		bool[] array = new bool[vgroup.Length];
		for (int i = 0; i < array.Length; i++)
		{
			array[i] = vgroup[i] == selPart;
		}
		return array;
	}

	private void SetTool(string name)
	{
		toolName = name;
		viewer.Tool = name;
		if (TglBox != null)
		{
			TglBox.IsChecked = name == "box";
			TglCut.IsChecked = name == "line";
		}
		((UIElement)ToolHint).Visibility = (Visibility)((name == "") ? 2 : 0);
		ToolHint.Text = ((name == "box") ? "Drag a box in the 3D view around the area you want. Everything inside it, even behind, becomes a new part." : ((name == "line") ? "Drag a line across the model. The smaller side becomes a new part. Flip side switches it." : ""));
		((FrameworkElement)VpMouse).Cursor = ((name == "") ? Cursors.Arrow : Cursors.Cross);
	}

	private void ClearToolCanvas()
	{
		((Panel)ToolCanvas).Children.Clear();
	}

	private void OnToolDrag(Point a, Point b, bool final)
	{
		//IL_001f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0024: Unknown result type (might be due to invalid IL or missing references)
		//IL_002a: Expected O, but got Unknown
		//IL_0094: Unknown result type (might be due to invalid IL or missing references)
		//IL_0099: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bf: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c5: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e8: Expected O, but got Unknown
		//IL_00e8: Unknown result type (might be due to invalid IL or missing references)
		//IL_00fa: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ff: Unknown result type (might be due to invalid IL or missing references)
		//IL_0109: Expected O, but got Unknown
		//IL_010b: Expected O, but got Unknown
		//IL_0154: Unknown result type (might be due to invalid IL or missing references)
		//IL_0159: Unknown result type (might be due to invalid IL or missing references)
		//IL_0166: Unknown result type (might be due to invalid IL or missing references)
		//IL_0173: Unknown result type (might be due to invalid IL or missing references)
		//IL_0180: Unknown result type (might be due to invalid IL or missing references)
		//IL_018d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0194: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a3: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b8: Unknown result type (might be due to invalid IL or missing references)
		//IL_01cc: Expected O, but got Unknown
		//IL_01d1: Expected O, but got Unknown
		((Panel)ToolCanvas).Children.Clear();
		SolidColorBrush stroke = new SolidColorBrush(Color.FromRgb((byte)244, (byte)244, (byte)244));
		if (toolName == "box")
		{
			double num = Math.Min((a).X, (b).X);
			double num2 = Math.Min((a).Y, (b).Y);
			double width = Math.Abs((a).X - (b).X);
			double height = Math.Abs((a).Y - (b).Y);
			Rectangle val = new Rectangle
			{
				Width = width,
				Height = height,
				Stroke = (Brush)(object)stroke,
				StrokeThickness = 1.2
			};
			DoubleCollection val2 = new DoubleCollection();
			val2.Add(4.0);
			val2.Add(3.0);
			((Shape)val).StrokeDashArray = val2;
			((Shape)val).Fill = (Brush)new SolidColorBrush(Color.FromArgb((byte)30, byte.MaxValue, byte.MaxValue, byte.MaxValue));
			Rectangle val3 = val;
			Canvas.SetLeft((UIElement)(object)val3, num);
			Canvas.SetTop((UIElement)(object)val3, num2);
			((Panel)ToolCanvas).Children.Add((UIElement)(object)val3);
		}
		else if (toolName == "line")
		{
			UIElementCollection children = ((Panel)ToolCanvas).Children;
			Line val4 = new Line
			{
				X1 = (a).X,
				Y1 = (a).Y,
				X2 = (b).X,
				Y2 = (b).Y,
				Stroke = (Brush)(object)stroke,
				StrokeThickness = 1.6
			};
			DoubleCollection val5 = new DoubleCollection();
			val5.Add(5.0);
			val5.Add(3.0);
			((Shape)val4).StrokeDashArray = val5;
			children.Add((UIElement)val4);
		}
		if (!final)
		{
			return;
		}
		((Panel)ToolCanvas).Children.Clear();
		Point[] array = viewer.ProjectModel();
		if (array == null || vertN == 0 || array.Length != vertN)
		{
			return;
		}
		bool[] array2 = viewer.UsedVertices();
		if (toolName == "box")
		{
			if (Math.Abs((a).X - (b).X) < 6.0 || Math.Abs((a).Y - (b).Y) < 6.0)
			{
				return;
			}
			double num3 = Math.Min((a).X, (b).X);
			double num4 = Math.Max((a).X, (b).X);
			double num5 = Math.Min((a).Y, (b).Y);
			double num6 = Math.Max((a).Y, (b).Y);
			bool[] array3 = new bool[vertN];
			int num7 = 0;
			for (int i = 0; i < vertN; i++)
			{
				if (array2[i] && (array[i]).X >= num3 && (array[i]).X <= num4 && (array[i]).Y >= num5 && (array[i]).Y <= num6)
				{
					array3[i] = true;
					num7++;
				}
			}
			if (num7 < 3)
			{
				Toast("Nothing inside that box. Try a bigger one.", ok: false);
			}
			else
			{
				AddCustom(array3, keepFlip: false);
			}
		}
		else
		{
			if (!(toolName == "line"))
			{
				return;
			}
			double num8 = (b).X - (a).X;
			double num9 = (b).Y - (a).Y;
			if (Math.Sqrt(num8 * num8 + num9 * num9) < 12.0)
			{
				return;
			}
			bool[] array4 = new bool[vertN];
			bool[] array5 = new bool[vertN];
			int num10 = 0;
			int num11 = 0;
			for (int j = 0; j < vertN; j++)
			{
				if (array2[j])
				{
					if (num8 * ((array[j]).Y - (a).Y) - num9 * ((array[j]).X - (a).X) >= 0.0)
					{
						array4[j] = true;
						num10++;
					}
					else
					{
						array5[j] = true;
						num11++;
					}
				}
			}
			if (num10 < 3 || num11 < 3)
			{
				Toast("That line doesn't split the model. Draw it across the part you want.", ok: false);
				return;
			}
			lineSideA = ((num10 <= num11) ? array4 : array5);
			lineSideB = ((num10 <= num11) ? array5 : array4);
			lineFlipped = false;
			lineTarget = AddCustom(lineSideA, keepFlip: true);
			((UIElement)BtnFlip).Visibility = (Visibility)0;
		}
	}

	private CustomPart AddCustom(bool[] mask, bool keepFlip)
	{
		CustomPart customPart = new CustomPart
		{
			Name = "Part " + (customs.Count + 1),
			Mask = mask
		};
		customs.Add(customPart);
		selPart = 100 + customs.Count - 1;
		RebuildChips();
		ShowPartOps();
		if (!keepFlip)
		{
			((UIElement)BtnFlip).Visibility = (Visibility)2;
		}
		Toast(customPart.Name + " made. Use the sliders to move it, or tick Hide to delete it.");
		return customPart;
	}

	private void FlipLine()
	{
		if (lineTarget != null && lineSideA != null)
		{
			lineFlipped = !lineFlipped;
			lineTarget.Mask = (lineFlipped ? lineSideB : lineSideA);
			if (selPart == 100 + customs.IndexOf(lineTarget))
			{
				RefreshHighlight();
			}
			if (!lineTarget.Op.IsDefault)
			{
				QueueEditRefit();
			}
		}
	}

	private void WirePartsUi()
	{
		//IL_000d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0017: Expected O, but got Unknown
		//IL_0024: Unknown result type (might be due to invalid IL or missing references)
		//IL_002e: Expected O, but got Unknown
		//IL_003b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0045: Expected O, but got Unknown
		//IL_0052: Unknown result type (might be due to invalid IL or missing references)
		//IL_005c: Expected O, but got Unknown
		//IL_0069: Unknown result type (might be due to invalid IL or missing references)
		//IL_0073: Expected O, but got Unknown
		//IL_0080: Unknown result type (might be due to invalid IL or missing references)
		//IL_008a: Expected O, but got Unknown
		//IL_0097: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a1: Expected O, but got Unknown
		//IL_00ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b8: Expected O, but got Unknown
		//IL_00c5: Unknown result type (might be due to invalid IL or missing references)
		//IL_00cf: Expected O, but got Unknown
		//IL_00dc: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e6: Expected O, but got Unknown
		//IL_00f3: Unknown result type (might be due to invalid IL or missing references)
		//IL_00fd: Expected O, but got Unknown
		//IL_010a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0114: Expected O, but got Unknown
		((ToggleButton)ChkUnlimited).Checked += (RoutedEventHandler)delegate
		{
			SetUnlimited(on: true);
		};
		((ToggleButton)ChkUnlimited).Unchecked += (RoutedEventHandler)delegate
		{
			SetUnlimited(on: false);
		};
		((ToggleButton)ChkMatchPose).Checked += (RoutedEventHandler)delegate
		{
			matchPose = true;
			QueueEditRefit();
		};
		((ToggleButton)ChkMatchPose).Unchecked += (RoutedEventHandler)delegate
		{
			matchPose = false;
			QueueEditRefit();
		};
		((ButtonBase)BtnPartsEdit).Click += (RoutedEventHandler)delegate
		{
			//IL_0006: Unknown result type (might be due to invalid IL or missing references)
			//IL_000c: Invalid comparison between Unknown and I4
			bool flag = (int)((UIElement)PartsEditor).Visibility > 0;
			((UIElement)PartsEditor).Visibility = (Visibility)((!flag) ? 2 : 0);
			((ContentControl)BtnPartsEdit).Content = (flag ? "Edit body parts  −" : "Edit body parts  +");
			if (flag)
			{
				Anim.In((FrameworkElement)(object)PartsEditor, 260.0, 8.0);
				if (!partsBuilt)
				{
					BuildPartsUi();
				}
			}
			if (!flag)
			{
				SetTool("");
			}
		};
		((ButtonBase)TglBox).Click += (RoutedEventHandler)delegate
		{
			SetTool(TglBox.IsChecked.GetValueOrDefault() ? "box" : "");
		};
		((ButtonBase)TglCut).Click += (RoutedEventHandler)delegate
		{
			SetTool(TglCut.IsChecked.GetValueOrDefault() ? "line" : "");
		};
		((ButtonBase)BtnFlip).Click += (RoutedEventHandler)delegate
		{
			FlipLine();
		};
		((ButtonBase)ChkHide).Click += (RoutedEventHandler)delegate
		{
			PartOp partOp5 = SelOp();
			if (partOp5 != null)
			{
				partOp5.Hide = ((ToggleButton)ChkHide).IsChecked.GetValueOrDefault();
				QueueEditRefit();
			}
		};
		((ButtonBase)BtnPartReset).Click += (RoutedEventHandler)delegate
		{
			PartOp partOp3 = SelOp();
			if (partOp3 != null)
			{
				PartOp partOp4 = new PartOp();
				partOp3.Hide = false;
				partOp3.Move = partOp4.Move;
				partOp3.Scale = 1.0;
				partOp3.Rot = partOp4.Rot;
				ShowPartOps();
				QueueEditRefit();
			}
		};
		((ButtonBase)BtnPartMirror).Click += (RoutedEventHandler)delegate
		{
			PartOp partOp = SelOp();
			if (partOp != null && selPart >= 2 && selPart <= 5)
			{
				int num = ((selPart % 2 == 0) ? (selPart + 1) : (selPart - 1));
				PartOp partOp2 = OpOf(num);
				partOp2.Hide = partOp.Hide;
				partOp2.Scale = partOp.Scale;
				partOp2.Move = new double[3]
				{
					0.0 - partOp.Move[0],
					partOp.Move[1],
					partOp.Move[2]
				};
				partOp2.Rot = new double[3]
				{
					partOp.Rot[0],
					0.0 - partOp.Rot[1],
					0.0 - partOp.Rot[2]
				};
				Toast("Copied to the " + groupNames[num].ToLowerInvariant());
				QueueEditRefit();
			}
		};
		((ButtonBase)BtnPartRemove).Click += (RoutedEventHandler)delegate
		{
			if (selPart >= 100)
			{
				customs.RemoveAt(selPart - 100);
				selPart = -1;
				RebuildChips();
				((UIElement)PartOps).Visibility = (Visibility)2;
				RefreshHighlight();
				QueueEditRefit();
				((UIElement)BtnFlip).Visibility = (Visibility)2;
			}
		};
		viewer.ToolDrag += OnToolDrag;
	}

	private void ShowMods()
	{
		modsMode = true;
		((UIElement)ExtView).Visibility = (Visibility)2;
		((UIElement)MarketView).Visibility = (Visibility)2;
		((UIElement)Wizard).Visibility = (Visibility)2;
		((UIElement)BtnMods).Visibility = (Visibility)2;
		((UIElement)ModsView).Visibility = (Visibility)0;
		Anim.In((FrameworkElement)(object)ModsView, 300.0, 10.0);
	}

	private void ShowWizard()
	{
		modsMode = false;
		((UIElement)ExtView).Visibility = (Visibility)2;
		((UIElement)MarketView).Visibility = (Visibility)2;
		((UIElement)ModsView).Visibility = (Visibility)2;
		((UIElement)Wizard).Visibility = (Visibility)0;
		((UIElement)BtnMods).Visibility = (Visibility)((modCount <= 0 && !anyOld) ? 2 : 0);
	}

	private async Task RouteMods(GameRow g)
	{
		if (g == null || !g.Supported)
		{
			modCount = 0;
			anyOld = false;
			ShowWizard();
			return;
		}
		await LoadMods(g);
		if (cur != null && !(cur.Id != g.Id))
		{
			if (modCount > 0 || anyOld)
			{
				ShowMods();
			}
			else
			{
				ShowWizard();
			}
		}
	}

	private async Task LoadMods(GameRow g)
	{
		try
		{
			JsonElement jsonElement = await api.Get("/api/mods?game=" + Uri.EscapeDataString(g.Id));
			if (cur == null || cur.Id != g.Id)
			{
				return;
			}
			List<ModRow> list = new List<ModRow>();
			foreach (JsonElement item in jsonElement.GetProperty("mods").EnumerateArray())
			{
				DateTimeOffset dateTimeOffset = DateTimeOffset.FromUnixTimeSeconds((long)item.GetProperty("created").GetDouble()).ToLocalTime();
				JsonElement value;
				string text = ((item.TryGetProperty("character", out value) && value.ValueKind == JsonValueKind.String) ? value.GetString() : "");
				list.Add(new ModRow
				{
					Id = item.GetProperty("id").GetString(),
					Name = item.GetProperty("name").GetString(),
					Pak = item.GetProperty("pak").GetString(),
					Active = item.GetProperty("active").GetBoolean(),
					Sub = (string.IsNullOrEmpty(text) ? "" : (text + "  ·  ")) + dateTimeOffset.ToString("MMM d, h:mm tt") + "  ·  " + ((double)item.GetProperty("size").GetInt64() / 1048576.0).ToString("0.#") + " MB"
				});
			}
			modCount = list.Count;
			bool boolean = jsonElement.GetProperty("anyInstalled").GetBoolean();
			anyOld = boolean && !list.Any((ModRow x) => x.Active);
			ModList.ItemsSource = list;
			((UIElement)OldInstallCard).Visibility = (Visibility)((!anyOld) ? 2 : 0);
			if (!modsMode)
			{
				((UIElement)BtnMods).Visibility = (Visibility)((modCount <= 0 && !anyOld) ? 2 : 0);
			}
		}
		catch (Exception ex)
		{
			App.Log("mods: " + ex);
		}
	}

	private async void OnModClick(object sender, RoutedEventArgs e)
	{
		object originalSource = e.OriginalSource;
		Button val = (Button)((originalSource is Button) ? originalSource : null);
		if (val == null)
		{
			return;
		}
		object dataContext = ((FrameworkElement)val).DataContext;
		if (!(dataContext is ModRow row) || cur == null)
		{
			return;
		}
		string text = ((FrameworkElement)val).Tag as string;
		try
		{
			switch (text)
			{
			case "install":
				((UIElement)ModList).IsEnabled = false;
				try
				{
					if (row.Active)
					{
						Toast("Taking out " + row.Name + "...");
						JsonElement jsonElement = await api.Post("/api/mod_uninstall", new Dictionary<string, object>
						{
							{ "game", cur.Id },
							{ "id", row.Id }
						});
						await api.Job(jsonElement.GetProperty("job").GetString(), null);
						Toast("Uninstalled " + row.Name);
					}
					else
					{
						Toast("Installing " + row.Name + "...");
						JsonElement jsonElement2 = await api.Post("/api/mod_install", new Dictionary<string, object>
						{
							{ "game", cur.Id },
							{ "id", row.Id },
							{ "name", row.Name }
						});
						if (jsonElement2.ValueKind == JsonValueKind.Object && jsonElement2.TryGetProperty("job", out var value))
						{
							await api.Job(value.GetString(), null);
						}
						Toast(row.Name + " installed. Launch the game!");
					}
				}
				finally
				{
					((UIElement)ModList).IsEnabled = true;
				}
				installed = false;
				await LoadMods(cur);
				break;
			case "save":
			{
				bool flag = cur.Engine == "unity";
				SaveFileDialog val2 = new SaveFileDialog
				{
					FileName = Regex_Safe(row.Name) + (flag ? ".modswap.zip" : "_P.pak"),
					Filter = (flag ? "ModSwap mod (*.zip)|*.zip|All files|*.*" : "Unreal mod (*.pak)|*.pak|All files|*.*"),
					Title = "Save a copy of this mod"
				};
				if (((CommonDialog)val2).ShowDialog((Window)(object)this).GetValueOrDefault())
				{
					File.Copy(row.Pak, ((FileDialog)val2).FileName, overwrite: true);
					Toast("Saved " + Path.GetFileName(((FileDialog)val2).FileName));
				}
				break;
			}
			case "delete":
				if ((int)MessageBox.Show((Window)(object)this, "Delete \"" + row.Name + "\"" + (row.Active ? " and take it out of the game" : "") + "?", "ModSwap", (MessageBoxButton)1, (MessageBoxImage)32) == 1)
				{
					await api.Post("/api/mod_delete", new Dictionary<string, object>
					{
						{ "game", cur.Id },
						{ "id", row.Id }
					});
					Toast("Deleted " + row.Name);
					await LoadMods(cur);
					if (modCount == 0 && !anyOld)
					{
						ShowWizard();
					}
				}
				break;
			}
		}
		catch (Exception ex)
		{
			Toast(Friendly(ex.Message).Item1, ok: false);
			App.Log("mod action: " + ex);
		}
	}

	private static string Regex_Safe(string s)
	{
		char[] bad = Path.GetInvalidFileNameChars();
		string text = new string(s.Select((char c) => (!bad.Contains(c)) ? c : '_').ToArray()).Trim();
		if (text.Length != 0)
		{
			return text;
		}
		return "mod";
	}

	private void WireModsUi()
	{
		//IL_0012: Unknown result type (might be due to invalid IL or missing references)
		//IL_001c: Expected O, but got Unknown
		//IL_0029: Unknown result type (might be due to invalid IL or missing references)
		//IL_0033: Expected O, but got Unknown
		//IL_0040: Unknown result type (might be due to invalid IL or missing references)
		//IL_004a: Expected O, but got Unknown
		//IL_0057: Unknown result type (might be due to invalid IL or missing references)
		//IL_0061: Expected O, but got Unknown
		//IL_006e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0078: Expected O, but got Unknown
		((UIElement)ModList).AddHandler(ButtonBase.ClickEvent, (Delegate)new RoutedEventHandler(OnModClick));
		((ButtonBase)BtnNewMod).Click += (RoutedEventHandler)delegate
		{
			ShowWizard();
		};
		((ButtonBase)BtnMods).Click += (RoutedEventHandler)async delegate
		{
			if (cur != null)
			{
				await LoadMods(cur);
				ShowMods();
			}
		};
		((ButtonBase)BtnRemoveOld).Click += (RoutedEventHandler)async delegate
		{
			if (cur == null)
			{
				return;
			}
			try
			{
				await api.Post("/api/restore", new Dictionary<string, object> { { "game", cur.Id } });
				Toast("Mod removed");
				await LoadMods(cur);
				if (modCount == 0)
				{
					ShowWizard();
				}
			}
			catch (Exception ex)
			{
				Toast(Friendly(ex.Message).Item1, ok: false);
			}
		};
		((ButtonBase)BtnSave).Click += (RoutedEventHandler)async delegate
		{
			await Install(install: false);
		};
	}

	private void StLog(string s)
	{
		try
		{
			File.AppendAllText(Path.Combine(stDir, "selftest.log"), DateTime.Now.ToString("HH:mm:ss ") + s + Environment.NewLine);
		}
		catch
		{
		}
	}

	private void Shot(string name)
	{
		//IL_0032: Unknown result type (might be due to invalid IL or missing references)
		//IL_0037: Unknown result type (might be due to invalid IL or missing references)
		//IL_003d: Expected O, but got Unknown
		//IL_0049: Unknown result type (might be due to invalid IL or missing references)
		//IL_004f: Expected O, but got Unknown
		try
		{
			((UIElement)this).UpdateLayout();
			int num = (int)((FrameworkElement)Root).ActualWidth;
			int num2 = (int)((FrameworkElement)Root).ActualHeight;
			RenderTargetBitmap val = new RenderTargetBitmap(num, num2, 96.0, 96.0, PixelFormats.Pbgra32);
			val.Render((Visual)(object)Root);
			PngBitmapEncoder val2 = new PngBitmapEncoder();
			((BitmapEncoder)val2).Frames.Add(BitmapFrame.Create((BitmapSource)(object)val));
			using (FileStream fileStream = File.Create(Path.Combine(stDir, name + ".png")))
			{
				((BitmapEncoder)val2).Save((Stream)fileStream);
			}
			StLog("shot " + name);
		}
		catch (Exception ex)
		{
			StLog("shot " + name + " failed: " + ex.Message);
		}
	}

	private async Task WaitFor(Func<bool> cond, int ms)
	{
		DateTime end = DateTime.UtcNow.AddMilliseconds(ms);
		while (!cond() && DateTime.UtcNow < end)
		{
			await Task.Delay(250);
		}
	}

	private async Task SelfTest()
	{
		string[] cfg = (from x in File.ReadAllLines(Path.Combine(Backend.AppDir, "selftest.txt"))
			select x.Trim() into x
			where x.Length > 0
			select x).ToArray();
		stDir = cfg[0];
		Directory.CreateDirectory(stDir);
		try
		{
			StLog("selftest start, games: " + string.Join(" | ", allGames.Select((GameRow g) => g.Name + " [" + g.Label + "]")));
			await Task.Delay(1500);
			Shot("1_library");
			GameRow g2 = allGames.FirstOrDefault((GameRow g) => g.Name.IndexOf(cfg[1], StringComparison.OrdinalIgnoreCase) >= 0);
			if (g2 == null)
			{
				StLog("game not found");
				return;
			}
			((Selector)GameList).SelectedItem = ((IEnumerable)((ItemsControl)GameList).Items).Cast<GameRow>().FirstOrDefault((GameRow g) => g.Id == g2.Id);
			await Task.Delay(1200);
			Shot("2_game");
			await WaitFor(() => charsReady, 720000);
			StLog("charsReady=" + charsReady);
			await Task.Delay(800);
			Shot("3_chars");
			if (charsReady)
			{
				await UploadPaths(new string[1] { cfg[2] });
				await WaitFor(() => fit.HasValue, 240000);
				StLog("fit=" + fit.HasValue + " viewerHasFit=" + viewer.HasFit);
				await Task.Delay(2500);
				Shot("4_fit");
				adj["yaw"] = 30.0;
				adj["width"] = 1.2;
				SyncSliders();
				LiveUpdate();
				await Task.Delay(600);
				Shot("5_live");
				((ToggleButton)ViewSide).IsChecked = true;
				await Task.Delay(1100);
				Shot("6_side");
				((ToggleButton)ViewTop).IsChecked = true;
				await Task.Delay(1100);
				Shot("7_top");
				((ToggleButton)ViewOrbit).IsChecked = true;
				await Task.Delay(1100);
				Shot("8_orbit");
				await Task.Delay(5000);
				Shot("9_refit");
				StLog("done");
			}
		}
		catch (Exception ex)
		{
			StLog("EXCEPTION " + ex);
		}
		finally
		{
			StLog("exit");
			Application.Current.Shutdown();
		}
	}

	[DebuggerNonUserCode]
	[GeneratedCode("PresentationBuildTasks", "8.0.11.0")]
	public void InitializeComponent()
	{
		if (!_contentLoaded)
		{
			_contentLoaded = true;
			Uri uri = new Uri("/ModSwap;component/mainwindow.xaml", UriKind.Relative);
			Application.LoadComponent((object)this, uri);
		}
	}

	[DebuggerNonUserCode]
	[GeneratedCode("PresentationBuildTasks", "8.0.11.0")]
	[EditorBrowsable(EditorBrowsableState.Never)]
	void IComponentConnector.Connect(int connectionId, object target)
	{
		//IL_0313: Unknown result type (might be due to invalid IL or missing references)
		//IL_031d: Expected O, but got Unknown
		//IL_0320: Unknown result type (might be due to invalid IL or missing references)
		//IL_032a: Expected O, but got Unknown
		//IL_032d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0337: Expected O, but got Unknown
		//IL_033a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0344: Expected O, but got Unknown
		//IL_0347: Unknown result type (might be due to invalid IL or missing references)
		//IL_0351: Expected O, but got Unknown
		//IL_0354: Unknown result type (might be due to invalid IL or missing references)
		//IL_035e: Expected O, but got Unknown
		//IL_0361: Unknown result type (might be due to invalid IL or missing references)
		//IL_036b: Expected O, but got Unknown
		//IL_036e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0378: Expected O, but got Unknown
		//IL_037b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0385: Expected O, but got Unknown
		//IL_0388: Unknown result type (might be due to invalid IL or missing references)
		//IL_0392: Expected O, but got Unknown
		//IL_0395: Unknown result type (might be due to invalid IL or missing references)
		//IL_039f: Expected O, but got Unknown
		//IL_03a2: Unknown result type (might be due to invalid IL or missing references)
		//IL_03ac: Expected O, but got Unknown
		//IL_03af: Unknown result type (might be due to invalid IL or missing references)
		//IL_03b9: Expected O, but got Unknown
		//IL_03bc: Unknown result type (might be due to invalid IL or missing references)
		//IL_03c6: Expected O, but got Unknown
		//IL_03c9: Unknown result type (might be due to invalid IL or missing references)
		//IL_03d3: Expected O, but got Unknown
		//IL_03d6: Unknown result type (might be due to invalid IL or missing references)
		//IL_03e0: Expected O, but got Unknown
		//IL_03e3: Unknown result type (might be due to invalid IL or missing references)
		//IL_03ed: Expected O, but got Unknown
		//IL_03f0: Unknown result type (might be due to invalid IL or missing references)
		//IL_03fa: Expected O, but got Unknown
		//IL_03fd: Unknown result type (might be due to invalid IL or missing references)
		//IL_0407: Expected O, but got Unknown
		//IL_040a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0414: Expected O, but got Unknown
		//IL_0417: Unknown result type (might be due to invalid IL or missing references)
		//IL_0421: Expected O, but got Unknown
		//IL_0424: Unknown result type (might be due to invalid IL or missing references)
		//IL_042e: Expected O, but got Unknown
		//IL_0431: Unknown result type (might be due to invalid IL or missing references)
		//IL_043b: Expected O, but got Unknown
		//IL_043e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0448: Expected O, but got Unknown
		//IL_044b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0455: Expected O, but got Unknown
		//IL_0458: Unknown result type (might be due to invalid IL or missing references)
		//IL_0462: Expected O, but got Unknown
		//IL_0465: Unknown result type (might be due to invalid IL or missing references)
		//IL_046f: Expected O, but got Unknown
		//IL_0472: Unknown result type (might be due to invalid IL or missing references)
		//IL_047c: Expected O, but got Unknown
		//IL_047f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0489: Expected O, but got Unknown
		//IL_048c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0496: Expected O, but got Unknown
		//IL_0499: Unknown result type (might be due to invalid IL or missing references)
		//IL_04a3: Expected O, but got Unknown
		//IL_04a6: Unknown result type (might be due to invalid IL or missing references)
		//IL_04b0: Expected O, but got Unknown
		//IL_04b3: Unknown result type (might be due to invalid IL or missing references)
		//IL_04bd: Expected O, but got Unknown
		//IL_04c0: Unknown result type (might be due to invalid IL or missing references)
		//IL_04ca: Expected O, but got Unknown
		//IL_04cd: Unknown result type (might be due to invalid IL or missing references)
		//IL_04d7: Expected O, but got Unknown
		//IL_04da: Unknown result type (might be due to invalid IL or missing references)
		//IL_04e4: Expected O, but got Unknown
		//IL_04e7: Unknown result type (might be due to invalid IL or missing references)
		//IL_04f1: Expected O, but got Unknown
		//IL_04f4: Unknown result type (might be due to invalid IL or missing references)
		//IL_04fe: Expected O, but got Unknown
		//IL_0501: Unknown result type (might be due to invalid IL or missing references)
		//IL_050b: Expected O, but got Unknown
		//IL_050e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0518: Expected O, but got Unknown
		//IL_051b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0525: Expected O, but got Unknown
		//IL_0528: Unknown result type (might be due to invalid IL or missing references)
		//IL_0532: Expected O, but got Unknown
		//IL_0535: Unknown result type (might be due to invalid IL or missing references)
		//IL_053f: Expected O, but got Unknown
		//IL_0542: Unknown result type (might be due to invalid IL or missing references)
		//IL_054c: Expected O, but got Unknown
		//IL_054f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0559: Expected O, but got Unknown
		//IL_055c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0566: Expected O, but got Unknown
		//IL_0569: Unknown result type (might be due to invalid IL or missing references)
		//IL_0573: Expected O, but got Unknown
		//IL_0576: Unknown result type (might be due to invalid IL or missing references)
		//IL_0580: Expected O, but got Unknown
		//IL_0583: Unknown result type (might be due to invalid IL or missing references)
		//IL_058d: Expected O, but got Unknown
		//IL_0590: Unknown result type (might be due to invalid IL or missing references)
		//IL_059a: Expected O, but got Unknown
		//IL_059d: Unknown result type (might be due to invalid IL or missing references)
		//IL_05a7: Expected O, but got Unknown
		//IL_05aa: Unknown result type (might be due to invalid IL or missing references)
		//IL_05b4: Expected O, but got Unknown
		//IL_05b7: Unknown result type (might be due to invalid IL or missing references)
		//IL_05c1: Expected O, but got Unknown
		//IL_05c4: Unknown result type (might be due to invalid IL or missing references)
		//IL_05ce: Expected O, but got Unknown
		//IL_05d1: Unknown result type (might be due to invalid IL or missing references)
		//IL_05db: Expected O, but got Unknown
		//IL_05de: Unknown result type (might be due to invalid IL or missing references)
		//IL_05e8: Expected O, but got Unknown
		//IL_05eb: Unknown result type (might be due to invalid IL or missing references)
		//IL_05f5: Expected O, but got Unknown
		//IL_05f8: Unknown result type (might be due to invalid IL or missing references)
		//IL_0602: Expected O, but got Unknown
		//IL_0605: Unknown result type (might be due to invalid IL or missing references)
		//IL_060f: Expected O, but got Unknown
		//IL_0612: Unknown result type (might be due to invalid IL or missing references)
		//IL_061c: Expected O, but got Unknown
		//IL_061f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0629: Expected O, but got Unknown
		//IL_062c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0636: Expected O, but got Unknown
		//IL_0639: Unknown result type (might be due to invalid IL or missing references)
		//IL_0643: Expected O, but got Unknown
		//IL_0646: Unknown result type (might be due to invalid IL or missing references)
		//IL_0650: Expected O, but got Unknown
		//IL_0653: Unknown result type (might be due to invalid IL or missing references)
		//IL_065d: Expected O, but got Unknown
		//IL_0660: Unknown result type (might be due to invalid IL or missing references)
		//IL_066a: Expected O, but got Unknown
		//IL_066d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0677: Expected O, but got Unknown
		//IL_067a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0684: Expected O, but got Unknown
		//IL_0687: Unknown result type (might be due to invalid IL or missing references)
		//IL_0691: Expected O, but got Unknown
		//IL_0694: Unknown result type (might be due to invalid IL or missing references)
		//IL_069e: Expected O, but got Unknown
		//IL_06a1: Unknown result type (might be due to invalid IL or missing references)
		//IL_06ab: Expected O, but got Unknown
		//IL_06ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_06b8: Expected O, but got Unknown
		//IL_06bb: Unknown result type (might be due to invalid IL or missing references)
		//IL_06c5: Expected O, but got Unknown
		//IL_06c8: Unknown result type (might be due to invalid IL or missing references)
		//IL_06d2: Expected O, but got Unknown
		//IL_06d5: Unknown result type (might be due to invalid IL or missing references)
		//IL_06df: Expected O, but got Unknown
		//IL_06e2: Unknown result type (might be due to invalid IL or missing references)
		//IL_06ec: Expected O, but got Unknown
		//IL_06ef: Unknown result type (might be due to invalid IL or missing references)
		//IL_06f9: Expected O, but got Unknown
		//IL_06fc: Unknown result type (might be due to invalid IL or missing references)
		//IL_0706: Expected O, but got Unknown
		//IL_0709: Unknown result type (might be due to invalid IL or missing references)
		//IL_0713: Expected O, but got Unknown
		//IL_0716: Unknown result type (might be due to invalid IL or missing references)
		//IL_0720: Expected O, but got Unknown
		//IL_0723: Unknown result type (might be due to invalid IL or missing references)
		//IL_072d: Expected O, but got Unknown
		//IL_0730: Unknown result type (might be due to invalid IL or missing references)
		//IL_073a: Expected O, but got Unknown
		//IL_073d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0747: Expected O, but got Unknown
		//IL_074a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0754: Expected O, but got Unknown
		//IL_0757: Unknown result type (might be due to invalid IL or missing references)
		//IL_0761: Expected O, but got Unknown
		//IL_0764: Unknown result type (might be due to invalid IL or missing references)
		//IL_076e: Expected O, but got Unknown
		//IL_0771: Unknown result type (might be due to invalid IL or missing references)
		//IL_077b: Expected O, but got Unknown
		//IL_077e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0788: Expected O, but got Unknown
		//IL_078b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0795: Expected O, but got Unknown
		//IL_0798: Unknown result type (might be due to invalid IL or missing references)
		//IL_07a2: Expected O, but got Unknown
		//IL_07a5: Unknown result type (might be due to invalid IL or missing references)
		//IL_07af: Expected O, but got Unknown
		//IL_07b2: Unknown result type (might be due to invalid IL or missing references)
		//IL_07bc: Expected O, but got Unknown
		//IL_07bf: Unknown result type (might be due to invalid IL or missing references)
		//IL_07c9: Expected O, but got Unknown
		//IL_07cc: Unknown result type (might be due to invalid IL or missing references)
		//IL_07d6: Expected O, but got Unknown
		//IL_07d9: Unknown result type (might be due to invalid IL or missing references)
		//IL_07e3: Expected O, but got Unknown
		//IL_07e6: Unknown result type (might be due to invalid IL or missing references)
		//IL_07f0: Expected O, but got Unknown
		//IL_07f3: Unknown result type (might be due to invalid IL or missing references)
		//IL_07fd: Expected O, but got Unknown
		//IL_0800: Unknown result type (might be due to invalid IL or missing references)
		//IL_080a: Expected O, but got Unknown
		//IL_080d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0817: Expected O, but got Unknown
		//IL_081a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0824: Expected O, but got Unknown
		//IL_0827: Unknown result type (might be due to invalid IL or missing references)
		//IL_0831: Expected O, but got Unknown
		//IL_0834: Unknown result type (might be due to invalid IL or missing references)
		//IL_083e: Expected O, but got Unknown
		//IL_0841: Unknown result type (might be due to invalid IL or missing references)
		//IL_084b: Expected O, but got Unknown
		//IL_084e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0858: Expected O, but got Unknown
		//IL_085b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0865: Expected O, but got Unknown
		//IL_0868: Unknown result type (might be due to invalid IL or missing references)
		//IL_0872: Expected O, but got Unknown
		//IL_0875: Unknown result type (might be due to invalid IL or missing references)
		//IL_087f: Expected O, but got Unknown
		//IL_0882: Unknown result type (might be due to invalid IL or missing references)
		//IL_088c: Expected O, but got Unknown
		//IL_088f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0899: Expected O, but got Unknown
		//IL_089c: Unknown result type (might be due to invalid IL or missing references)
		//IL_08a6: Expected O, but got Unknown
		//IL_08a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_08b3: Expected O, but got Unknown
		//IL_08b6: Unknown result type (might be due to invalid IL or missing references)
		//IL_08c0: Expected O, but got Unknown
		//IL_08c3: Unknown result type (might be due to invalid IL or missing references)
		//IL_08cd: Expected O, but got Unknown
		//IL_08d0: Unknown result type (might be due to invalid IL or missing references)
		//IL_08da: Expected O, but got Unknown
		//IL_08dd: Unknown result type (might be due to invalid IL or missing references)
		//IL_08e7: Expected O, but got Unknown
		//IL_08ea: Unknown result type (might be due to invalid IL or missing references)
		//IL_08f4: Expected O, but got Unknown
		//IL_08f7: Unknown result type (might be due to invalid IL or missing references)
		//IL_0901: Expected O, but got Unknown
		//IL_0904: Unknown result type (might be due to invalid IL or missing references)
		//IL_090e: Expected O, but got Unknown
		//IL_0911: Unknown result type (might be due to invalid IL or missing references)
		//IL_091b: Expected O, but got Unknown
		//IL_091e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0928: Expected O, but got Unknown
		//IL_092b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0935: Expected O, but got Unknown
		//IL_0938: Unknown result type (might be due to invalid IL or missing references)
		//IL_0942: Expected O, but got Unknown
		//IL_0945: Unknown result type (might be due to invalid IL or missing references)
		//IL_094f: Expected O, but got Unknown
		//IL_0952: Unknown result type (might be due to invalid IL or missing references)
		//IL_095c: Expected O, but got Unknown
		//IL_095f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0969: Expected O, but got Unknown
		//IL_096c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0976: Expected O, but got Unknown
		//IL_0979: Unknown result type (might be due to invalid IL or missing references)
		//IL_0983: Expected O, but got Unknown
		//IL_0986: Unknown result type (might be due to invalid IL or missing references)
		//IL_0990: Expected O, but got Unknown
		//IL_0993: Unknown result type (might be due to invalid IL or missing references)
		//IL_099d: Expected O, but got Unknown
		//IL_09a0: Unknown result type (might be due to invalid IL or missing references)
		//IL_09aa: Expected O, but got Unknown
		//IL_09ad: Unknown result type (might be due to invalid IL or missing references)
		//IL_09b7: Expected O, but got Unknown
		//IL_09ba: Unknown result type (might be due to invalid IL or missing references)
		//IL_09c4: Expected O, but got Unknown
		//IL_09c7: Unknown result type (might be due to invalid IL or missing references)
		//IL_09d1: Expected O, but got Unknown
		//IL_09d4: Unknown result type (might be due to invalid IL or missing references)
		//IL_09de: Expected O, but got Unknown
		//IL_09e1: Unknown result type (might be due to invalid IL or missing references)
		//IL_09eb: Expected O, but got Unknown
		//IL_09ee: Unknown result type (might be due to invalid IL or missing references)
		//IL_09f8: Expected O, but got Unknown
		//IL_09fb: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a05: Expected O, but got Unknown
		//IL_0a08: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a12: Expected O, but got Unknown
		//IL_0a15: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a1f: Expected O, but got Unknown
		//IL_0a22: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a2c: Expected O, but got Unknown
		//IL_0a2f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a39: Expected O, but got Unknown
		//IL_0a3c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a46: Expected O, but got Unknown
		//IL_0a49: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a53: Expected O, but got Unknown
		//IL_0a56: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a60: Expected O, but got Unknown
		//IL_0a63: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a6d: Expected O, but got Unknown
		//IL_0a70: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a7a: Expected O, but got Unknown
		//IL_0a7d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a87: Expected O, but got Unknown
		//IL_0a8a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a94: Expected O, but got Unknown
		//IL_0a97: Unknown result type (might be due to invalid IL or missing references)
		//IL_0aa1: Expected O, but got Unknown
		//IL_0aa4: Unknown result type (might be due to invalid IL or missing references)
		//IL_0aae: Expected O, but got Unknown
		//IL_0ab1: Unknown result type (might be due to invalid IL or missing references)
		//IL_0abb: Expected O, but got Unknown
		//IL_0abe: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ac8: Expected O, but got Unknown
		//IL_0acb: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ad5: Expected O, but got Unknown
		//IL_0ad8: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ae2: Expected O, but got Unknown
		//IL_0ae5: Unknown result type (might be due to invalid IL or missing references)
		//IL_0aef: Expected O, but got Unknown
		//IL_0af2: Unknown result type (might be due to invalid IL or missing references)
		//IL_0afc: Expected O, but got Unknown
		//IL_0aff: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b09: Expected O, but got Unknown
		//IL_0b0c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b16: Expected O, but got Unknown
		//IL_0b19: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b23: Expected O, but got Unknown
		//IL_0b26: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b30: Expected O, but got Unknown
		//IL_0b33: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b3d: Expected O, but got Unknown
		//IL_0b40: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b4a: Expected O, but got Unknown
		//IL_0b4d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b57: Expected O, but got Unknown
		//IL_0b5a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b64: Expected O, but got Unknown
		//IL_0b67: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b71: Expected O, but got Unknown
		//IL_0b74: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b7e: Expected O, but got Unknown
		//IL_0b81: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b8b: Expected O, but got Unknown
		//IL_0b8e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b98: Expected O, but got Unknown
		//IL_0b9b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ba5: Expected O, but got Unknown
		//IL_0ba8: Unknown result type (might be due to invalid IL or missing references)
		//IL_0bb2: Expected O, but got Unknown
		//IL_0bb5: Unknown result type (might be due to invalid IL or missing references)
		//IL_0bbf: Expected O, but got Unknown
		//IL_0bc2: Unknown result type (might be due to invalid IL or missing references)
		//IL_0bcc: Expected O, but got Unknown
		//IL_0bcf: Unknown result type (might be due to invalid IL or missing references)
		//IL_0bd9: Expected O, but got Unknown
		//IL_0bdc: Unknown result type (might be due to invalid IL or missing references)
		//IL_0be6: Expected O, but got Unknown
		//IL_0be9: Unknown result type (might be due to invalid IL or missing references)
		//IL_0bf3: Expected O, but got Unknown
		//IL_0bf6: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c00: Expected O, but got Unknown
		//IL_0c03: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c0d: Expected O, but got Unknown
		//IL_0c10: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c1a: Expected O, but got Unknown
		//IL_0c1d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c27: Expected O, but got Unknown
		//IL_0c2a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c34: Expected O, but got Unknown
		//IL_0c37: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c41: Expected O, but got Unknown
		//IL_0c44: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c4e: Expected O, but got Unknown
		//IL_0c51: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c5b: Expected O, but got Unknown
		//IL_0c5e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c68: Expected O, but got Unknown
		//IL_0c6b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c75: Expected O, but got Unknown
		//IL_0c78: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c82: Expected O, but got Unknown
		//IL_0c85: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c8f: Expected O, but got Unknown
		//IL_0c92: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c9c: Expected O, but got Unknown
		//IL_0c9f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ca9: Expected O, but got Unknown
		//IL_0cac: Unknown result type (might be due to invalid IL or missing references)
		//IL_0cb6: Expected O, but got Unknown
		//IL_0cb9: Unknown result type (might be due to invalid IL or missing references)
		//IL_0cc3: Expected O, but got Unknown
		//IL_0cc6: Unknown result type (might be due to invalid IL or missing references)
		//IL_0cd0: Expected O, but got Unknown
		//IL_0cd3: Unknown result type (might be due to invalid IL or missing references)
		//IL_0cdd: Expected O, but got Unknown
		switch (connectionId)
		{
		case 1:
			Root = (Grid)target;
			break;
		case 2:
			BtnMin = (Button)target;
			break;
		case 3:
			BtnMax = (Button)target;
			break;
		case 4:
			BtnClose = (Button)target;
			break;
		case 5:
			BtnScan = (Button)target;
			break;
		case 6:
			BtnAdd = (Button)target;
			break;
		case 7:
			SearchRow = (Grid)target;
			break;
		case 8:
			SearchBox = (TextBox)target;
			break;
		case 9:
			SearchHint = (TextBlock)target;
			break;
		case 10:
			FilterAll = (RadioButton)target;
			break;
		case 11:
			FilterSwap = (RadioButton)target;
			break;
		case 12:
			GameList = (ListBox)target;
			break;
		case 13:
			LibFoot = (TextBlock)target;
			break;
		case 14:
			BtnShowAll = (Button)target;
			break;
		case 15:
			EmptyView = (Grid)target;
			break;
		case 16:
			HomeSub = (TextBlock)target;
			break;
		case 17:
			BtnScan2 = (Button)target;
			break;
		case 18:
			BtnAdd2 = (Button)target;
			break;
		case 19:
			HomeSearch = (TextBox)target;
			break;
		case 20:
			HomeSearchHint = (TextBlock)target;
			break;
		case 21:
			HomeScroll = (ScrollViewer)target;
			break;
		case 22:
			GameGrid = (ItemsControl)target;
			break;
		case 23:
			HomeEmpty = (TextBlock)target;
			break;
		case 24:
			BtnShowAll2 = (Button)target;
			break;
		case 25:
			HowCard = (Border)target;
			break;
		case 26:
			BtnDiag = (Button)target;
			break;
		case 27:
			FormatsText = (TextBlock)target;
			break;
		case 28:
			WorkView = (Grid)target;
			break;
		case 29:
			BtnBack = (Button)target;
			break;
		case 30:
			BtnMods = (Button)target;
			break;
		case 31:
			GameTitle = (TextBlock)target;
			break;
		case 32:
			EngineText = (TextBlock)target;
			break;
		case 33:
			SwapTag = (Border)target;
			break;
		case 34:
			SwapTagText = (TextBlock)target;
			break;
		case 35:
			GamePath = (TextBlock)target;
			break;
		case 36:
			BtnMarket = (Button)target;
			break;
		case 37:
			BtnExt = (Button)target;
			break;
		case 38:
			BtnRedetect = (Button)target;
			break;
		case 39:
			BtnRemove = (Button)target;
			break;
		case 40:
			ModsView = (Grid)target;
			break;
		case 41:
			BtnNewMod = (Button)target;
			break;
		case 42:
			ModList = (ItemsControl)target;
			break;
		case 43:
			OldInstallCard = (Border)target;
			break;
		case 44:
			BtnRemoveOld = (Button)target;
			break;
		case 45:
			ExtView = (Grid)target;
			break;
		case 46:
			ExtIntro = (TextBlock)target;
			break;
		case 47:
			BtnExtSwap = (Button)target;
			break;
		case 48:
			ExtDrop = (Grid)target;
			break;
		case 49:
			ExtRect = (Rectangle)target;
			break;
		case 50:
			ExtBrush = (SolidColorBrush)target;
			break;
		case 51:
			ExtBypass = (Border)target;
			break;
		case 52:
			ExtBypassTitle = (TextBlock)target;
			break;
		case 53:
			ExtBypassText = (TextBlock)target;
			break;
		case 54:
			ExtEmpty = (TextBlock)target;
			break;
		case 55:
			ExtList = (ItemsControl)target;
			break;
		case 56:
			BtnExtFolder = (Button)target;
			break;
		case 57:
			BtnReset2 = (Button)target;
			break;
		case 58:
			MarketView = (Grid)target;
			break;
		case 59:
			MarketIntro = (TextBlock)target;
			break;
		case 60:
			BtnMarketBack = (Button)target;
			break;
		case 61:
			MkLib = (RadioButton)target;
			break;
		case 62:
			MkSf = (RadioButton)target;
			break;
		case 63:
			MarketSearch = (TextBox)target;
			break;
		case 64:
			MarketSearchHint = (TextBlock)target;
			break;
		case 65:
			MarketChips = (WrapPanel)target;
			break;
		case 66:
			SfConnect = (Border)target;
			break;
		case 67:
			SfTitle = (TextBlock)target;
			break;
		case 68:
			SfText = (TextBlock)target;
			break;
		case 69:
			SfTokenRow = (StackPanel)target;
			break;
		case 70:
			SfToken = (TextBox)target;
			break;
		case 71:
			SfTokenHint = (TextBlock)target;
			break;
		case 72:
			BtnSfConnect = (Button)target;
			break;
		case 73:
			BtnSfGet = (Button)target;
			break;
		case 74:
			BtnSfOff = (Button)target;
			break;
		case 75:
			MarketNote = (TextBlock)target;
			break;
		case 76:
			MarketEmpty = (Border)target;
			break;
		case 77:
			MarketEmptyText = (TextBlock)target;
			break;
		case 78:
			MarketList = (ItemsControl)target;
			break;
		case 79:
			BtnSfMore = (Button)target;
			break;
		case 80:
			BtnMarketFolder = (Button)target;
			break;
		case 81:
			Wizard = (Grid)target;
			break;
		case 82:
			StepsScroll = (ScrollViewer)target;
			break;
		case 83:
			Step1 = (Border)target;
			break;
		case 84:
			Num1 = (TextBlock)target;
			break;
		case 85:
			Step1Title = (TextBlock)target;
			break;
		case 86:
			CharStatus = (TextBlock)target;
			break;
		case 87:
			CharSearchBox = (Grid)target;
			break;
		case 88:
			CharSearch = (TextBox)target;
			break;
		case 89:
			CharSearchHint = (TextBlock)target;
			break;
		case 90:
			CharCats = (WrapPanel)target;
			break;
		case 91:
			CatAll = (RadioButton)target;
			break;
		case 92:
			CatPeople = (RadioButton)target;
			break;
		case 93:
			CatVehicles = (RadioButton)target;
			break;
		case 94:
			CatWeapons = (RadioButton)target;
			break;
		case 95:
			CatObjects = (RadioButton)target;
			break;
		case 96:
			CatHidden = (ToggleButton)target;
			break;
		case 97:
			CharEmpty = (TextBlock)target;
			break;
		case 98:
			CharList = (ListBox)target;
			break;
		case 99:
			CharFoot = (Grid)target;
			break;
		case 100:
			CharCount = (TextBlock)target;
			break;
		case 101:
			BtnRescan = (Button)target;
			break;
		case 102:
			Step2 = (Border)target;
			break;
		case 103:
			Num2 = (TextBlock)target;
			break;
		case 104:
			BtnClearModel = (Button)target;
			break;
		case 105:
			DropZone = (Grid)target;
			break;
		case 106:
			DropRect = (Rectangle)target;
			break;
		case 107:
			DropBrush = (SolidColorBrush)target;
			break;
		case 108:
			DropTitle = (TextBlock)target;
			break;
		case 109:
			DropSub = (TextBlock)target;
			break;
		case 110:
			FileChips = (ItemsControl)target;
			break;
		case 111:
			ModelSum = (TextBlock)target;
			break;
		case 112:
			StatsPanel = (Grid)target;
			break;
		case 113:
			StatV = (TextBlock)target;
			break;
		case 114:
			StatT = (TextBlock)target;
			break;
		case 115:
			StatM = (TextBlock)target;
			break;
		case 116:
			StatX = (TextBlock)target;
			break;
		case 117:
			Thumbs = (ItemsControl)target;
			break;
		case 118:
			BtnAdv = (Button)target;
			break;
		case 119:
			AdvPanel = (StackPanel)target;
			break;
		case 120:
			PartsPanel = (StackPanel)target;
			break;
		case 121:
			BtnPartsAll = (Button)target;
			break;
		case 122:
			BtnPartsNone = (Button)target;
			break;
		case 123:
			PartsList = (ItemsControl)target;
			break;
		case 124:
			AxisPanel = (Grid)target;
			break;
		case 125:
			UpLabel = (TextBlock)target;
			break;
		case 126:
			UpCombo = (ComboBox)target;
			break;
		case 127:
			FwdLabel = (TextBlock)target;
			break;
		case 128:
			FwdCombo = (ComboBox)target;
			break;
		case 129:
			Step3 = (Border)target;
			break;
		case 130:
			Num3 = (TextBlock)target;
			break;
		case 131:
			FitHint = (TextBlock)target;
			break;
		case 132:
			FitControls = (StackPanel)target;
			break;
		case 133:
			TargetBox = (StackPanel)target;
			break;
		case 134:
			TargetLabel = (TextBlock)target;
			break;
		case 135:
			TargetBar = (WrapPanel)target;
			break;
		case 136:
			BtnRotL = (Button)target;
			break;
		case 137:
			BtnRotR = (Button)target;
			break;
		case 138:
			BtnTurn = (Button)target;
			break;
		case 139:
			BtnReset = (Button)target;
			break;
		case 140:
			ChkUnlimited = (CheckBox)target;
			break;
		case 141:
			ChkMatchPose = (CheckBox)target;
			break;
		case 142:
			SliderHost = (StackPanel)target;
			break;
		case 143:
			BtnMore = (Button)target;
			break;
		case 144:
			SliderMore = (StackPanel)target;
			break;
		case 145:
			BtnPartsEdit = (Button)target;
			break;
		case 146:
			PartsEditor = (StackPanel)target;
			break;
		case 147:
			PartChips = (WrapPanel)target;
			break;
		case 148:
			TglBox = (ToggleButton)target;
			break;
		case 149:
			TglCut = (ToggleButton)target;
			break;
		case 150:
			BtnFlip = (Button)target;
			break;
		case 151:
			ToolHint = (TextBlock)target;
			break;
		case 152:
			PartOps = (StackPanel)target;
			break;
		case 153:
			ChkHide = (CheckBox)target;
			break;
		case 154:
			PartSliders = (StackPanel)target;
			break;
		case 155:
			BtnPartReset = (Button)target;
			break;
		case 156:
			BtnPartMirror = (Button)target;
			break;
		case 157:
			BtnPartRemove = (Button)target;
			break;
		case 158:
			Step4 = (Border)target;
			break;
		case 159:
			Num4 = (TextBlock)target;
			break;
		case 160:
			InstallHint = (TextBlock)target;
			break;
		case 161:
			InstallControls = (StackPanel)target;
			break;
		case 162:
			ModName = (TextBox)target;
			break;
		case 163:
			BtnInstall = (Button)target;
			break;
		case 164:
			BtnSave = (Button)target;
			break;
		case 165:
			StagePanel = (Grid)target;
			break;
		case 166:
			Stage0 = (Border)target;
			break;
		case 167:
			Stage1 = (Border)target;
			break;
		case 168:
			Stage2 = (Border)target;
			break;
		case 169:
			Stage3 = (Border)target;
			break;
		case 170:
			LogText = (TextBlock)target;
			break;
		case 171:
			DoneCard = (Border)target;
			break;
		case 172:
			BtnUndo = (Button)target;
			break;
		case 173:
			VpHost = (Grid)target;
			break;
		case 174:
			VpMouse = (Border)target;
			break;
		case 175:
			ToolCanvas = (Canvas)target;
			break;
		case 176:
			Placeholder = (StackPanel)target;
			break;
		case 177:
			PlaceholderSub = (TextBlock)target;
			break;
		case 178:
			ViewFront = (RadioButton)target;
			break;
		case 179:
			ViewSide = (RadioButton)target;
			break;
		case 180:
			ViewTop = (RadioButton)target;
			break;
		case 181:
			ViewOrbit = (RadioButton)target;
			break;
		case 182:
			TglOutline = (ToggleButton)target;
			break;
		case 183:
			TglModel = (ToggleButton)target;
			break;
		case 184:
			BusyPill = (Border)target;
			break;
		case 185:
			BusyText = (TextBlock)target;
			break;
		case 186:
			BusyBar = (Grid)target;
			break;
		case 187:
			BusyRect = (Rectangle)target;
			break;
		case 188:
			BusyShift = (TranslateTransform)target;
			break;
		case 189:
			FwdInfo = (TextBlock)target;
			break;
		case 190:
			ToastHost = (StackPanel)target;
			break;
		case 191:
			Boot = (Grid)target;
			break;
		case 192:
			BootText = (TextBlock)target;
			break;
		case 193:
			BootShift = (TranslateTransform)target;
			break;
		default:
			_contentLoaded = true;
			break;
		}
	}
}

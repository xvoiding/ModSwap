using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Media.Media3D;

namespace ModSwap;

public class Viewer3D
{
	private readonly PerspectiveCamera cam = new PerspectiveCamera
	{
		FieldOfView = 32.0,
		NearPlaneDistance = 50.0,
		FarPlaneDistance = 3000.0
	};

	private readonly DirectionalLight head = new DirectionalLight(Color.FromRgb((byte)235, (byte)235, (byte)235), new Vector3D(0.0, 0.0, -1.0));

	private readonly ModelVisual3D modelHost = new ModelVisual3D();

	private readonly ModelVisual3D hiHost = new ModelVisual3D();

	private Point3D[] curPts;

	private int[] curTri;

	private MeshGeometry3D curGeo;

	private bool[] usedV;

	public string Tool = "";

	private readonly ModelVisual3D ghostHost = new ModelVisual3D();

	private readonly ModelVisual3D gridHost = new ModelVisual3D();

	private Model3D ghostModel;

	private Model3D gridModel;

	private Model3D modelModel;

	private readonly AxisAngleRotation3D yawRot = new AxisAngleRotation3D(new Vector3D(0.0, 1.0, 0.0), 0.0);

	private readonly AxisAngleRotation3D pitchRot = new AxisAngleRotation3D(new Vector3D(1.0, 0.0, 0.0), 0.0);

	private readonly AxisAngleRotation3D rollRot = new AxisAngleRotation3D(new Vector3D(0.0, 0.0, 1.0), 0.0);

	private readonly RotateTransform3D pitchT;

	private readonly RotateTransform3D rollT;

	private readonly ScaleTransform3D scale = new ScaleTransform3D(1.0, 1.0, 1.0);

	private readonly TranslateTransform3D trans = new TranslateTransform3D(0.0, 0.0, 0.0);

	private Point3D p3 = new Point3D(0.0, 0.0, 0.0);

	private double h = 170.0;

	private double ground;

	private double az;

	private double el = 0.04;

	private double dist = 500.0;

	private Point3D target = new Point3D(0.0, 85.0, 0.0);

	private bool framed;

	public bool ShowOutline = true;

	public bool ShowModel = true;

	private EventHandler tick;

	private Point last;

	private bool orbiting;

	private bool panning;

	private bool tooling;

	private Point toolStart;

	public Viewport3D VP { get; private set; }

	public bool HasFit { get; private set; }

	public event Action<Point, Point, bool> ToolDrag;

	public Viewer3D()
	{
		//IL_0001: Unknown result type (might be due to invalid IL or missing references)
		//IL_0006: Unknown result type (might be due to invalid IL or missing references)
		//IL_0015: Unknown result type (might be due to invalid IL or missing references)
		//IL_0024: Unknown result type (might be due to invalid IL or missing references)
		//IL_0038: Expected O, but got Unknown
		//IL_0048: Unknown result type (might be due to invalid IL or missing references)
		//IL_0068: Unknown result type (might be due to invalid IL or missing references)
		//IL_006d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0077: Expected O, but got Unknown
		//IL_0078: Unknown result type (might be due to invalid IL or missing references)
		//IL_0082: Expected O, but got Unknown
		//IL_0083: Unknown result type (might be due to invalid IL or missing references)
		//IL_008d: Expected O, but got Unknown
		//IL_0099: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a3: Expected O, but got Unknown
		//IL_00a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ae: Expected O, but got Unknown
		//IL_00ca: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d8: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e2: Expected O, but got Unknown
		//IL_00fe: Unknown result type (might be due to invalid IL or missing references)
		//IL_010c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0116: Expected O, but got Unknown
		//IL_0132: Unknown result type (might be due to invalid IL or missing references)
		//IL_0140: Unknown result type (might be due to invalid IL or missing references)
		//IL_014a: Expected O, but got Unknown
		//IL_0166: Unknown result type (might be due to invalid IL or missing references)
		//IL_0170: Expected O, but got Unknown
		//IL_018c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0196: Expected O, but got Unknown
		//IL_01b2: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b7: Unknown result type (might be due to invalid IL or missing references)
		//IL_0205: Unknown result type (might be due to invalid IL or missing references)
		//IL_020a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0224: Unknown result type (might be due to invalid IL or missing references)
		//IL_0229: Unknown result type (might be due to invalid IL or missing references)
		//IL_0230: Unknown result type (might be due to invalid IL or missing references)
		//IL_0241: Expected O, but got Unknown
		//IL_0241: Unknown result type (might be due to invalid IL or missing references)
		//IL_0247: Expected O, but got Unknown
		//IL_0253: Unknown result type (might be due to invalid IL or missing references)
		//IL_0258: Unknown result type (might be due to invalid IL or missing references)
		//IL_0262: Expected O, but got Unknown
		//IL_027f: Unknown result type (might be due to invalid IL or missing references)
		//IL_029f: Unknown result type (might be due to invalid IL or missing references)
		//IL_02a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_02ae: Expected O, but got Unknown
		//IL_02b9: Unknown result type (might be due to invalid IL or missing references)
		//IL_02be: Unknown result type (might be due to invalid IL or missing references)
		//IL_02ca: Expected O, but got Unknown
		//IL_030c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0312: Expected O, but got Unknown
		//IL_031e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0328: Expected O, but got Unknown
		//IL_032f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0339: Expected O, but got Unknown
		//IL_0340: Unknown result type (might be due to invalid IL or missing references)
		//IL_034a: Expected O, but got Unknown
		VP = new Viewport3D
		{
			ClipToBounds = true,
			Camera = (Camera)(object)cam
		};
		Model3DGroup val = new Model3DGroup();
		val.Children.Add((Model3D)new AmbientLight(Color.FromRgb((byte)110, (byte)110, (byte)110)));
		val.Children.Add((Model3D)(object)head);
		val.Children.Add((Model3D)new DirectionalLight(Color.FromRgb((byte)70, (byte)70, (byte)70), new Vector3D(-0.6, -0.3, 0.8)));
		VP.Children.Add((Visual3D)new ModelVisual3D
		{
			Content = (Model3D)(object)val
		});
		VP.Children.Add((Visual3D)(object)gridHost);
		VP.Children.Add((Visual3D)(object)modelHost);
		VP.Children.Add((Visual3D)(object)ghostHost);
		Transform3DGroup val2 = new Transform3DGroup();
		val2.Children.Add((Transform3D)new RotateTransform3D((Rotation3D)(object)yawRot));
		pitchT = new RotateTransform3D((Rotation3D)(object)pitchRot);
		rollT = new RotateTransform3D((Rotation3D)(object)rollRot);
		val2.Children.Add((Transform3D)(object)pitchT);
		val2.Children.Add((Transform3D)(object)rollT);
		val2.Children.Add((Transform3D)(object)scale);
		val2.Children.Add((Transform3D)(object)trans);
		modelHost.Transform = (Transform3D)(object)val2;
		hiHost.Transform = (Transform3D)(object)val2;
		VP.Children.Add((Visual3D)(object)hiHost);
		UpdateCam();
	}

	private static float[] F32(string b64)
	{
		byte[] array = Convert.FromBase64String(b64);
		float[] array2 = new float[array.Length / 4];
		Buffer.BlockCopy(array, 0, array2, 0, array.Length);
		return array2;
	}

	private static uint[] U32(string b64)
	{
		byte[] array = Convert.FromBase64String(b64);
		uint[] array2 = new uint[array.Length / 4];
		Buffer.BlockCopy(array, 0, array2, 0, array.Length);
		return array2;
	}

	private static Point3D P(float[] a, int i)
	{
		//IL_0016: Unknown result type (might be due to invalid IL or missing references)
		return new Point3D((double)a[3 * i], (double)a[3 * i + 2], (double)a[3 * i + 1]);
	}

	private static MeshGeometry3D MakeMesh(Point3D[] pts, int[] tri, Point[] uv)
	{
		//IL_0000: Unknown result type (might be due to invalid IL or missing references)
		//IL_0006: Expected O, but got Unknown
		//IL_0008: Unknown result type (might be due to invalid IL or missing references)
		//IL_0012: Expected O, but got Unknown
		//IL_0014: Unknown result type (might be due to invalid IL or missing references)
		//IL_001e: Expected O, but got Unknown
		//IL_0023: Unknown result type (might be due to invalid IL or missing references)
		//IL_002d: Expected O, but got Unknown
		//IL_0043: Unknown result type (might be due to invalid IL or missing references)
		//IL_0048: Unknown result type (might be due to invalid IL or missing references)
		//IL_0051: Unknown result type (might be due to invalid IL or missing references)
		//IL_005d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0062: Unknown result type (might be due to invalid IL or missing references)
		//IL_0064: Unknown result type (might be due to invalid IL or missing references)
		//IL_0066: Unknown result type (might be due to invalid IL or missing references)
		//IL_006b: Unknown result type (might be due to invalid IL or missing references)
		//IL_006d: Unknown result type (might be due to invalid IL or missing references)
		//IL_006f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0074: Unknown result type (might be due to invalid IL or missing references)
		//IL_0079: Unknown result type (might be due to invalid IL or missing references)
		//IL_0086: Unknown result type (might be due to invalid IL or missing references)
		//IL_008b: Unknown result type (might be due to invalid IL or missing references)
		//IL_008d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0092: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ab: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ce: Unknown result type (might be due to invalid IL or missing references)
		//IL_0110: Unknown result type (might be due to invalid IL or missing references)
		//IL_0115: Unknown result type (might be due to invalid IL or missing references)
		//IL_01de: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e5: Expected O, but got Unknown
		//IL_01ef: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f6: Unknown result type (might be due to invalid IL or missing references)
		MeshGeometry3D val = new MeshGeometry3D();
		val.Positions = new Point3DCollection((IEnumerable<Point3D>)pts);
		val.TriangleIndices = new Int32Collection((IEnumerable<int>)tri);
		if (uv != null)
		{
			val.TextureCoordinates = new PointCollection((IEnumerable<Point>)uv);
		}
		Vector3D[] array = (Vector3D[])(object)new Vector3D[pts.Length];
		for (int i = 0; i + 2 < tri.Length; i += 3)
		{
			Point3D val2 = pts[tri[i]];
			Point3D val3 = pts[tri[i + 1]];
			Point3D val4 = pts[tri[i + 2]];
			Vector3D val5 = Vector3D.CrossProduct(val3 - val2, val4 - val2);
			ref Vector3D reference = ref array[tri[i]];
			reference += val5;
			ref Vector3D reference2 = ref array[tri[i + 1]];
			reference2 += val5;
			ref Vector3D reference3 = ref array[tri[i + 2]];
			reference3 += val5;
		}
		double num = 0.0;
		double num2 = 0.0;
		double num3 = 0.0;
		for (int j = 0; j < pts.Length; j++)
		{
			Point3D val6 = pts[j];
			num += (val6).X;
			num2 += (val6).Y;
			num3 += (val6).Z;
		}
		num /= (double)pts.Length;
		num2 /= (double)pts.Length;
		num3 /= (double)pts.Length;
		double num4 = 0.0;
		for (int k = 0; k < pts.Length; k++)
		{
			(array[k]).Normalize();
			num4 += (array[k]).X * ((pts[k]).X - num) + (array[k]).Z * ((pts[k]).Z - num3);
		}
		double num5 = ((!(num4 < 0.0)) ? 1 : (-1));
		Vector3DCollection val7 = new Vector3DCollection(pts.Length);
		for (int l = 0; l < pts.Length; l++)
		{
			val7.Add(array[l] * num5);
		}
		val.Normals = val7;
		((Freezable)val).Freeze();
		return val;
	}

	public void SetFit(JsonElement r)
	{
		//IL_0056: Unknown result type (might be due to invalid IL or missing references)
		//IL_005b: Unknown result type (might be due to invalid IL or missing references)
		//IL_010a: Unknown result type (might be due to invalid IL or missing references)
		//IL_010f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0172: Unknown result type (might be due to invalid IL or missing references)
		//IL_0179: Expected O, but got Unknown
		//IL_018a: Unknown result type (might be due to invalid IL or missing references)
		//IL_018f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0199: Expected O, but got Unknown
		//IL_0194: Unknown result type (might be due to invalid IL or missing references)
		//IL_019b: Expected O, but got Unknown
		//IL_01b2: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b7: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c4: Expected O, but got Unknown
		//IL_01d8: Unknown result type (might be due to invalid IL or missing references)
		//IL_01dd: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e7: Expected O, but got Unknown
		//IL_01e2: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e9: Expected O, but got Unknown
		//IL_0204: Unknown result type (might be due to invalid IL or missing references)
		//IL_0209: Unknown result type (might be due to invalid IL or missing references)
		//IL_0216: Expected O, but got Unknown
		//IL_02d1: Unknown result type (might be due to invalid IL or missing references)
		//IL_02d6: Unknown result type (might be due to invalid IL or missing references)
		//IL_0315: Unknown result type (might be due to invalid IL or missing references)
		//IL_031a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0335: Unknown result type (might be due to invalid IL or missing references)
		//IL_033a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0373: Unknown result type (might be due to invalid IL or missing references)
		//IL_0378: Unknown result type (might be due to invalid IL or missing references)
		//IL_037e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0385: Unknown result type (might be due to invalid IL or missing references)
		//IL_03aa: Unknown result type (might be due to invalid IL or missing references)
		//IL_03b0: Unknown result type (might be due to invalid IL or missing references)
		//IL_03bb: Expected O, but got Unknown
		//IL_03b6: Unknown result type (might be due to invalid IL or missing references)
		//IL_03bb: Unknown result type (might be due to invalid IL or missing references)
		//IL_03c6: Expected O, but got Unknown
		//IL_03c1: Unknown result type (might be due to invalid IL or missing references)
		//IL_03c8: Expected O, but got Unknown
		//IL_0427: Unknown result type (might be due to invalid IL or missing references)
		//IL_042c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0439: Expected O, but got Unknown
		//IL_04da: Unknown result type (might be due to invalid IL or missing references)
		//IL_04df: Unknown result type (might be due to invalid IL or missing references)
		JsonElement property = r.GetProperty("info").GetProperty("pivot");
		double @double = property[0].GetDouble();
		double double2 = property[1].GetDouble();
		double double3 = property[2].GetDouble();
		p3 = new Point3D(@double, double3, double2);
		h = r.GetProperty("height").GetDouble();
		if (h < 10.0)
		{
			h = 170.0;
		}
		JsonElement property2 = r.GetProperty("orig");
		float[] array = F32(property2.GetProperty("pos").GetString());
		uint[] array2 = U32(property2.GetProperty("idx").GetString());
		int num = array.Length / 3;
		Point3D[] array3 = (Point3D[])(object)new Point3D[num];
		double num2 = double.MaxValue;
		for (int i = 0; i < num; i++)
		{
			array3[i] = P(array, i);
			if ((array3[i]).Y < num2)
			{
				num2 = (array3[i]).Y;
			}
		}
		ground = num2;
		int[] array4 = new int[array2.Length];
		for (int j = 0; j < array2.Length; j++)
		{
			array4[j] = (int)array2[j];
		}
		Model3DGroup val = new Model3DGroup();
		DiffuseMaterial val2 = new DiffuseMaterial((Brush)new SolidColorBrush(Color.FromArgb((byte)22, byte.MaxValue, byte.MaxValue, byte.MaxValue)));
		MeshGeometry3D val3 = MakeMesh(array3, array4, null);
		val.Children.Add((Model3D)new GeometryModel3D((Geometry3D)(object)val3, (Material)(object)val2)
		{
			BackMaterial = (Material)(object)val2
		});
		EmissiveMaterial val4 = new EmissiveMaterial((Brush)new SolidColorBrush(Color.FromArgb((byte)235, byte.MaxValue, byte.MaxValue, byte.MaxValue)));
		val.Children.Add((Model3D)new GeometryModel3D((Geometry3D)(object)BuildEdges(array3, array4, 0.28), (Material)(object)val4)
		{
			BackMaterial = (Material)(object)val4
		});
		val.Children.Add(BuildArrow(@double, ground, double2));
		ghostModel = (Model3D)(object)val;
		gridModel = BuildGrid(ground, @double, double2);
		JsonElement property3 = r.GetProperty("new");
		float[] array5 = F32(property3.GetProperty("pos").GetString());
		uint[] array6 = U32(property3.GetProperty("idx").GetString());
		float[] array7 = F32(property3.GetProperty("uv").GetString());
		int num3 = array5.Length / 3;
		Point3D[] array8 = (Point3D[])(object)new Point3D[num3];
		Point[] array9 = (Point[])(object)new Point[num3];
		for (int k = 0; k < num3; k++)
		{
			Point3D val5 = P(array5, k);
			array8[k] = new Point3D((val5).X - (p3).X, (val5).Y - (p3).Y, (val5).Z - (p3).Z);
			array9[k] = new Point((double)array7[2 * k], (double)array7[2 * k + 1]);
		}
		int[] array10 = new int[array6.Length];
		for (int l = 0; l < array6.Length; l++)
		{
			array10[l] = (int)array6[l];
		}
		BitmapImage val6 = new BitmapImage();
		val6.BeginInit();
		val6.CacheOption = (BitmapCacheOption)1;
		val6.StreamSource = new MemoryStream(Convert.FromBase64String(r.GetProperty("atlas").GetString()));
		val6.EndInit();
		((Freezable)val6).Freeze();
		ImageBrush val7 = new ImageBrush((ImageSource)val6);
		((Freezable)val7).Freeze();
		DiffuseMaterial val8 = new DiffuseMaterial((Brush)val7);
		curGeo = MakeMesh(array8, array10, array9);
		curPts = array8;
		curTri = array10;
		usedV = new bool[num3];
		int[] array11 = array10;
		foreach (int num4 in array11)
		{
			usedV[num4] = true;
		}
		modelModel = (Model3D)new GeometryModel3D((Geometry3D)(object)curGeo, (Material)(object)val8)
		{
			BackMaterial = (Material)(object)val8
		};
		Live(1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
		HasFit = true;
		ApplyVisibility();
		if (!framed)
		{
			framed = true;
			target = new Point3D((p3).X, ground + h * 0.5, (p3).Z);
			dist = h * 2.9;
			UpdateCam();
		}
		else
		{
			UpdateCam();
		}
	}

	private static MeshGeometry3D BuildEdges(Point3D[] pts, int[] tri, double w)
	{
		//IL_00e1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ff: Unknown result type (might be due to invalid IL or missing references)
		//IL_0104: Unknown result type (might be due to invalid IL or missing references)
		//IL_0106: Unknown result type (might be due to invalid IL or missing references)
		//IL_0108: Unknown result type (might be due to invalid IL or missing references)
		//IL_010d: Unknown result type (might be due to invalid IL or missing references)
		//IL_010f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0111: Unknown result type (might be due to invalid IL or missing references)
		//IL_0116: Unknown result type (might be due to invalid IL or missing references)
		//IL_011b: Unknown result type (might be due to invalid IL or missing references)
		//IL_013a: Unknown result type (might be due to invalid IL or missing references)
		//IL_013c: Unknown result type (might be due to invalid IL or missing references)
		//IL_024d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0258: Unknown result type (might be due to invalid IL or missing references)
		//IL_02d0: Unknown result type (might be due to invalid IL or missing references)
		//IL_02d5: Unknown result type (might be due to invalid IL or missing references)
		//IL_02e3: Unknown result type (might be due to invalid IL or missing references)
		//IL_02e8: Unknown result type (might be due to invalid IL or missing references)
		//IL_02ea: Unknown result type (might be due to invalid IL or missing references)
		//IL_02ec: Unknown result type (might be due to invalid IL or missing references)
		//IL_02ee: Unknown result type (might be due to invalid IL or missing references)
		//IL_02f3: Unknown result type (might be due to invalid IL or missing references)
		//IL_0473: Unknown result type (might be due to invalid IL or missing references)
		//IL_0478: Unknown result type (might be due to invalid IL or missing references)
		//IL_047b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0485: Expected O, but got Unknown
		//IL_0485: Unknown result type (might be due to invalid IL or missing references)
		//IL_0488: Unknown result type (might be due to invalid IL or missing references)
		//IL_0492: Expected O, but got Unknown
		//IL_0492: Unknown result type (might be due to invalid IL or missing references)
		//IL_0499: Expected O, but got Unknown
		//IL_0365: Unknown result type (might be due to invalid IL or missing references)
		//IL_0343: Unknown result type (might be due to invalid IL or missing references)
		//IL_036a: Unknown result type (might be due to invalid IL or missing references)
		//IL_036c: Unknown result type (might be due to invalid IL or missing references)
		//IL_036e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0370: Unknown result type (might be due to invalid IL or missing references)
		//IL_0375: Unknown result type (might be due to invalid IL or missing references)
		//IL_037e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0381: Unknown result type (might be due to invalid IL or missing references)
		//IL_0386: Unknown result type (might be due to invalid IL or missing references)
		//IL_0388: Unknown result type (might be due to invalid IL or missing references)
		//IL_038a: Unknown result type (might be due to invalid IL or missing references)
		//IL_038c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0391: Unknown result type (might be due to invalid IL or missing references)
		//IL_039a: Unknown result type (might be due to invalid IL or missing references)
		//IL_039d: Unknown result type (might be due to invalid IL or missing references)
		//IL_03a2: Unknown result type (might be due to invalid IL or missing references)
		//IL_03ac: Unknown result type (might be due to invalid IL or missing references)
		//IL_03ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_03b5: Unknown result type (might be due to invalid IL or missing references)
		//IL_03b7: Unknown result type (might be due to invalid IL or missing references)
		//IL_03ca: Unknown result type (might be due to invalid IL or missing references)
		//IL_03cf: Unknown result type (might be due to invalid IL or missing references)
		//IL_03dc: Unknown result type (might be due to invalid IL or missing references)
		//IL_03de: Unknown result type (might be due to invalid IL or missing references)
		//IL_03e0: Unknown result type (might be due to invalid IL or missing references)
		//IL_03ec: Unknown result type (might be due to invalid IL or missing references)
		//IL_03ee: Unknown result type (might be due to invalid IL or missing references)
		//IL_03f0: Unknown result type (might be due to invalid IL or missing references)
		//IL_03fc: Unknown result type (might be due to invalid IL or missing references)
		//IL_03fe: Unknown result type (might be due to invalid IL or missing references)
		//IL_0400: Unknown result type (might be due to invalid IL or missing references)
		//IL_040c: Unknown result type (might be due to invalid IL or missing references)
		//IL_040e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0410: Unknown result type (might be due to invalid IL or missing references)
		int num = pts.Length;
		int[] array = new int[num];
		Dictionary<long, int> dictionary = new Dictionary<long, int>();
		for (int i = 0; i < num; i++)
		{
			long key = ((long)Math.Round((pts[i]).X * 20.0) & 0x1FFFFF) | (((long)Math.Round((pts[i]).Y * 20.0) & 0x1FFFFF) << 21) | (((long)Math.Round((pts[i]).Z * 20.0) & 0x1FFFFF) << 42);
			if (!dictionary.TryGetValue(key, out var value))
			{
				value = i;
				dictionary[key] = i;
			}
			array[i] = value;
		}
		int num2 = tri.Length / 3;
		Vector3D[] array2 = (Vector3D[])(object)new Vector3D[num2];
		Dictionary<long, int[]> dictionary2 = new Dictionary<long, int[]>();
		for (int j = 0; j < num2; j++)
		{
			Point3D val = pts[tri[3 * j]];
			Point3D val2 = pts[tri[3 * j + 1]];
			Point3D val3 = pts[tri[3 * j + 2]];
			Vector3D val4 = Vector3D.CrossProduct(val2 - val, val3 - val);
			if ((val4).LengthSquared > 1E-12)
			{
				(val4).Normalize();
			}
			array2[j] = val4;
			for (int k = 0; k < 3; k++)
			{
				int num3 = tri[3 * j + k];
				int num4 = tri[3 * j + (k + 1) % 3];
				int num5 = array[num3];
				int num6 = array[num4];
				if (num5 == num6)
				{
					continue;
				}
				long key2 = ((num5 < num6) ? (((long)num5 << 32) | (uint)num6) : (((long)num6 << 32) | (uint)num5));
				if (!dictionary2.TryGetValue(key2, out var value2))
				{
					dictionary2[key2] = new int[5] { num3, num4, j, -1, 1 };
				}
				else
				{
					if (value2[4] == 1)
					{
						value2[3] = j;
					}
					value2[4]++;
				}
			}
		}
		List<int[]> list = new List<int[]>();
		double num7 = Math.Cos(Math.PI * 17.0 / 90.0);
		foreach (int[] value3 in dictionary2.Values)
		{
			if (value3[4] == 1)
			{
				list.Add(value3);
			}
			else if (value3[4] == 2 && Vector3D.DotProduct(array2[value3[2]], array2[value3[3]]) < num7)
			{
				list.Add(value3);
			}
		}
		int num8 = ((list.Count <= 11000) ? 1 : ((list.Count + 10999) / 11000));
		List<Point3D> list2 = new List<Point3D>();
		List<int> list3 = new List<int>();
		for (int l = 0; l < list.Count; l += num8)
		{
			Point3D val5 = pts[list[l][0]];
			Point3D val6 = pts[list[l][1]];
			Vector3D val7 = val6 - val5;
			if (!((val7).LengthSquared < 1E-10))
			{
				(val7).Normalize();
				Vector3D val8 = ((Math.Abs((val7).Y) > 0.9) ? new Vector3D(1.0, 0.0, 0.0) : new Vector3D(0.0, 1.0, 0.0));
				Vector3D val9 = Vector3D.CrossProduct(val7, val8);
				(val9).Normalize();
				val9 *= w;
				Vector3D val10 = Vector3D.CrossProduct(val7, val9);
				(val10).Normalize();
				val10 *= w;
				Vector3D[] array3 = (Vector3D[])(object)new Vector3D[2] { val9, val10 };
				foreach (Vector3D val11 in array3)
				{
					int count = list2.Count;
					list2.Add(val5 - val11);
					list2.Add(val5 + val11);
					list2.Add(val6 + val11);
					list2.Add(val6 - val11);
					list3.AddRange(new int[6]
					{
						count,
						count + 1,
						count + 2,
						count,
						count + 2,
						count + 3
					});
				}
			}
		}
		MeshGeometry3D val12 = new MeshGeometry3D
		{
			Positions = new Point3DCollection((IEnumerable<Point3D>)list2),
			TriangleIndices = new Int32Collection((IEnumerable<int>)list3)
		};
		((Freezable)val12).Freeze();
		return val12;
	}

	private static void Quad(List<Point3D> P3, List<int> I, Point3D a, Point3D b, Point3D c, Point3D d)
	{
		//IL_0008: Unknown result type (might be due to invalid IL or missing references)
		//IL_000f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0016: Unknown result type (might be due to invalid IL or missing references)
		//IL_001e: Unknown result type (might be due to invalid IL or missing references)
		int count = P3.Count;
		P3.Add(a);
		P3.Add(b);
		P3.Add(c);
		P3.Add(d);
		I.AddRange(new int[6]
		{
			count,
			count + 1,
			count + 2,
			count,
			count + 2,
			count + 3
		});
	}

	private Model3D BuildGrid(double y, double cx, double cz)
	{
		//IL_0041: Unknown result type (might be due to invalid IL or missing references)
		//IL_0051: Unknown result type (might be due to invalid IL or missing references)
		//IL_0061: Unknown result type (might be due to invalid IL or missing references)
		//IL_0071: Unknown result type (might be due to invalid IL or missing references)
		//IL_0088: Unknown result type (might be due to invalid IL or missing references)
		//IL_0098: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a8: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b8: Unknown result type (might be due to invalid IL or missing references)
		//IL_00da: Unknown result type (might be due to invalid IL or missing references)
		//IL_00df: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00eb: Expected O, but got Unknown
		//IL_00eb: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ed: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f7: Expected O, but got Unknown
		//IL_00f7: Unknown result type (might be due to invalid IL or missing references)
		//IL_010e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0113: Unknown result type (might be due to invalid IL or missing references)
		//IL_011d: Expected O, but got Unknown
		//IL_0118: Unknown result type (might be due to invalid IL or missing references)
		//IL_011f: Expected O, but got Unknown
		//IL_0126: Expected O, but got Unknown
		//IL_0121: Unknown result type (might be due to invalid IL or missing references)
		//IL_0126: Unknown result type (might be due to invalid IL or missing references)
		//IL_012f: Expected O, but got Unknown
		List<Point3D> list = new List<Point3D>();
		List<int> list2 = new List<int>();
		double num = 220.0;
		double num2 = 20.0;
		double num3 = 0.16;
		for (double num4 = 0.0 - num; num4 <= num + 0.1; num4 += num2)
		{
			Quad(list, list2, new Point3D(cx - num, y, cz + num4 - num3), new Point3D(cx + num, y, cz + num4 - num3), new Point3D(cx + num, y, cz + num4 + num3), new Point3D(cx - num, y, cz + num4 + num3));
			Quad(list, list2, new Point3D(cx + num4 - num3, y, cz - num), new Point3D(cx + num4 + num3, y, cz - num), new Point3D(cx + num4 + num3, y, cz + num), new Point3D(cx + num4 - num3, y, cz + num));
		}
		MeshGeometry3D val = new MeshGeometry3D
		{
			Positions = new Point3DCollection((IEnumerable<Point3D>)list),
			TriangleIndices = new Int32Collection((IEnumerable<int>)list2)
		};
		((Freezable)val).Freeze();
		EmissiveMaterial val2 = new EmissiveMaterial((Brush)new SolidColorBrush(Color.FromArgb((byte)34, byte.MaxValue, byte.MaxValue, byte.MaxValue)));
		return (Model3D)new GeometryModel3D((Geometry3D)val, (Material)(object)val2)
		{
			BackMaterial = (Material)(object)val2
		};
	}

	private Model3D BuildArrow(double cx, double y0, double cz)
	{
		//IL_006a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0074: Unknown result type (might be due to invalid IL or missing references)
		//IL_0080: Unknown result type (might be due to invalid IL or missing references)
		//IL_008c: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00db: Unknown result type (might be due to invalid IL or missing references)
		//IL_0105: Unknown result type (might be due to invalid IL or missing references)
		//IL_010a: Unknown result type (might be due to invalid IL or missing references)
		//IL_010d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0117: Expected O, but got Unknown
		//IL_0117: Unknown result type (might be due to invalid IL or missing references)
		//IL_011a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0124: Expected O, but got Unknown
		//IL_0124: Unknown result type (might be due to invalid IL or missing references)
		//IL_012f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0136: Expected O, but got Unknown
		//IL_013d: Expected O, but got Unknown
		//IL_0138: Unknown result type (might be due to invalid IL or missing references)
		//IL_013d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0146: Expected O, but got Unknown
		double num = y0 + 0.7;
		double num2 = cz + h * 0.3;
		double num3 = h * 0.2;
		double num4 = h * 0.012;
		double num5 = h * 0.045;
		List<Point3D> list = new List<Point3D>();
		List<int> list2 = new List<int>();
		Quad(list, list2, new Point3D(cx - num4, num, num2), new Point3D(cx + num4, num, num2), new Point3D(cx + num4, num, num2 + num3), new Point3D(cx - num4, num, num2 + num3));
		int count = list.Count;
		list.Add(new Point3D(cx - num5, num, num2 + num3));
		list.Add(new Point3D(cx + num5, num, num2 + num3));
		list.Add(new Point3D(cx, num, num2 + num3 + num5 * 1.7));
		list2.AddRange(new int[3]
		{
			count,
			count + 1,
			count + 2
		});
		MeshGeometry3D val = new MeshGeometry3D
		{
			Positions = new Point3DCollection((IEnumerable<Point3D>)list),
			TriangleIndices = new Int32Collection((IEnumerable<int>)list2)
		};
		((Freezable)val).Freeze();
		EmissiveMaterial val2 = new EmissiveMaterial((Brush)(object)Brushes.White);
		return (Model3D)new GeometryModel3D((Geometry3D)val, (Material)(object)val2)
		{
			BackMaterial = (Material)(object)val2
		};
	}

	public void Live(double sx, double sy, double sz, double yawDeg, double pitchDeg, double rollDeg, double dx, double dy, double dz)
	{
		scale.ScaleX = sx;
		scale.ScaleY = sy;
		scale.ScaleZ = sz;
		yawRot.Angle = 0.0 - yawDeg;
		pitchRot.Angle = pitchDeg;
		rollRot.Angle = 0.0 - rollDeg;
		RotateTransform3D obj = pitchT;
		double centerY = (rollT.CenterY = h * 0.5);
		obj.CenterY = centerY;
		trans.OffsetX = (p3).X + dx;
		trans.OffsetY = (p3).Y + dz;
		trans.OffsetZ = (p3).Z + dy;
	}

	public void Clear()
	{
		ghostModel = (gridModel = (modelModel = null));
		HasFit = false;
		framed = false;
		ghostHost.Content = null;
		gridHost.Content = null;
		modelHost.Content = null;
		hiHost.Content = null;
		curPts = null;
		curTri = null;
		curGeo = null;
	}

	public void SetOutline(bool on)
	{
		ShowOutline = on;
		ApplyVisibility();
	}

	public void SetModel(bool on)
	{
		ShowModel = on;
		ApplyVisibility();
	}

	private void ApplyVisibility()
	{
		ghostHost.Content = (ShowOutline ? ghostModel : null);
		gridHost.Content = gridModel;
		modelHost.Content = (ShowModel ? modelModel : null);
	}

	public bool[] UsedVertices()
	{
		return usedV ?? new bool[0];
	}

	public void SetHighlight(bool[] mask)
	{
		//IL_00e8: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ed: Unknown result type (might be due to invalid IL or missing references)
		//IL_015e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0163: Unknown result type (might be due to invalid IL or missing references)
		//IL_0178: Unknown result type (might be due to invalid IL or missing references)
		//IL_017d: Unknown result type (might be due to invalid IL or missing references)
		//IL_017f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0189: Expected O, but got Unknown
		//IL_0189: Unknown result type (might be due to invalid IL or missing references)
		//IL_018b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0195: Expected O, but got Unknown
		//IL_0196: Expected O, but got Unknown
		//IL_01ad: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b2: Unknown result type (might be due to invalid IL or missing references)
		//IL_01bc: Expected O, but got Unknown
		//IL_01b7: Unknown result type (might be due to invalid IL or missing references)
		//IL_01bd: Expected O, but got Unknown
		//IL_01c5: Unknown result type (might be due to invalid IL or missing references)
		//IL_01ca: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d6: Expected O, but got Unknown
		if (mask == null || curPts == null || curGeo == null || mask.Length != curPts.Length)
		{
			hiHost.Content = null;
			return;
		}
		List<int> list = new List<int>();
		for (int i = 0; i + 2 < curTri.Length; i += 3)
		{
			if ((mask[curTri[i]] ? 1 : 0) + (mask[curTri[i + 1]] ? 1 : 0) + (mask[curTri[i + 2]] ? 1 : 0) >= 2)
			{
				list.Add(curTri[i]);
				list.Add(curTri[i + 1]);
				list.Add(curTri[i + 2]);
			}
		}
		if (list.Count == 0)
		{
			hiHost.Content = null;
			return;
		}
		Point3D[] array = (Point3D[])(object)new Point3D[curPts.Length];
		for (int j = 0; j < array.Length; j++)
		{
			Vector3D val = curGeo.Normals[j];
			array[j] = new Point3D((curPts[j]).X + (val).X * 0.35, (curPts[j]).Y + (val).Y * 0.35, (curPts[j]).Z + (val).Z * 0.35);
		}
		MeshGeometry3D val2 = new MeshGeometry3D
		{
			Positions = new Point3DCollection((IEnumerable<Point3D>)array),
			TriangleIndices = new Int32Collection((IEnumerable<int>)list)
		};
		((Freezable)val2).Freeze();
		EmissiveMaterial val3 = new EmissiveMaterial((Brush)new SolidColorBrush(Color.FromArgb((byte)110, byte.MaxValue, byte.MaxValue, byte.MaxValue)));
		hiHost.Content = (Model3D)new GeometryModel3D((Geometry3D)(object)val2, (Material)(object)val3)
		{
			BackMaterial = (Material)(object)val3
		};
	}

	public Point[] ProjectModel()
	{
		//IL_0042: Unknown result type (might be due to invalid IL or missing references)
		//IL_0047: Unknown result type (might be due to invalid IL or missing references)
		//IL_004f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0056: Unknown result type (might be due to invalid IL or missing references)
		//IL_005b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0060: Unknown result type (might be due to invalid IL or missing references)
		//IL_0068: Unknown result type (might be due to invalid IL or missing references)
		//IL_0069: Unknown result type (might be due to invalid IL or missing references)
		//IL_006a: Unknown result type (might be due to invalid IL or missing references)
		//IL_006f: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b3: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00db: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00eb: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f4: Unknown result type (might be due to invalid IL or missing references)
		//IL_012b: Unknown result type (might be due to invalid IL or missing references)
		//IL_012d: Unknown result type (might be due to invalid IL or missing references)
		//IL_013b: Unknown result type (might be due to invalid IL or missing references)
		//IL_013d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0183: Unknown result type (might be due to invalid IL or missing references)
		//IL_0188: Unknown result type (might be due to invalid IL or missing references)
		//IL_011f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0124: Unknown result type (might be due to invalid IL or missing references)
		if (curPts == null)
		{
			return null;
		}
		double actualWidth = ((FrameworkElement)VP).ActualWidth;
		double actualHeight = ((FrameworkElement)VP).ActualHeight;
		if (actualWidth < 10.0 || actualHeight < 10.0)
		{
			return null;
		}
		Vector3D lookDirection = ((ProjectionCamera)cam).LookDirection;
		(lookDirection).Normalize();
		Vector3D val = Vector3D.CrossProduct(lookDirection, ((ProjectionCamera)cam).UpDirection);
		(val).Normalize();
		Vector3D val2 = Vector3D.CrossProduct(val, lookDirection);
		(val2).Normalize();
		double num = Math.Tan(cam.FieldOfView * Math.PI / 360.0);
		double num2 = actualWidth / actualHeight;
		Matrix3D value = modelHost.Transform.Value;
		Point[] array = (Point[])(object)new Point[curPts.Length];
		for (int i = 0; i < array.Length; i++)
		{
			Vector3D val3 = (value).Transform(curPts[i]) - ((ProjectionCamera)cam).Position;
			double num3 = Vector3D.DotProduct(val3, lookDirection);
			if (num3 < 0.001)
			{
				array[i] = new Point(-1000000.0, -1000000.0);
				continue;
			}
			double num4 = Vector3D.DotProduct(val3, val) / (num3 * num);
			double num5 = Vector3D.DotProduct(val3, val2) / (num3 * num / num2);
			array[i] = new Point((num4 * 0.5 + 0.5) * actualWidth, (0.5 - num5 * 0.5) * actualHeight);
		}
		return array;
	}

	private void UpdateCam()
	{
		//IL_0092: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ef: Unknown result type (might be due to invalid IL or missing references)
		double num = Math.Cos(el);
		double num2 = Math.Sin(el);
		double num3 = Math.Sin(az);
		double num4 = Math.Cos(az);
		Vector3D val = default(Vector3D);
		val = new Vector3D(num3 * num, num2, num4 * num);
		((ProjectionCamera)cam).Position = new Point3D((target).X + (val).X * dist, (target).Y + (val).Y * dist, (target).Z + (val).Z * dist);
		((ProjectionCamera)cam).LookDirection = -val;
		((ProjectionCamera)cam).UpDirection = new Vector3D((0.0 - num3) * num2, num, (0.0 - num4) * num2);
		head.Direction = new Vector3D(0.0 - (val).X, 0.0 - (val).Y - 0.25, 0.0 - (val).Z);
		double num5 = Math.Max(h * 1.15, 320.0) * 1.35;
		((ProjectionCamera)cam).NearPlaneDistance = Math.Max(dist * 0.05, dist - num5);
		((ProjectionCamera)cam).FarPlaneDistance = dist + num5;
	}

	public void SetView(string name)
	{
		//IL_00b3: Unknown result type (might be due to invalid IL or missing references)
		double eaz = 0.0;
		double eel = 0.04;
		switch (name)
		{
		case "side":
			eaz = -Math.PI / 2.0;
			break;
		case "top":
			eaz = Math.PI;
			eel = 1.5707;
			break;
		case "orbit":
			eaz = 0.72;
			eel = 0.28;
			break;
		}
		Tween(eaz, eel, h * 2.9, new Point3D((p3).X, ground + h * 0.5, (p3).Z));
	}

	private void Tween(double eaz, double eel, double edist, Point3D etarget)
	{
		//IL_001c: Unknown result type (might be due to invalid IL or missing references)
		//IL_001e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0063: Unknown result type (might be due to invalid IL or missing references)
		//IL_0068: Unknown result type (might be due to invalid IL or missing references)
		if (tick != null)
		{
			CompositionTarget.Rendering -= tick;
			tick = null;
		}
		double a0 = az;
		double e2 = el;
		double d0 = dist;
		Point3D t0 = target;
		DateTime s = DateTime.UtcNow;
		double da;
		for (da = eaz - a0; da > Math.PI; da -= Math.PI * 2.0)
		{
		}
		for (; da < -Math.PI; da += Math.PI * 2.0)
		{
		}
		tick = delegate
		{
			//IL_0126: Unknown result type (might be due to invalid IL or missing references)
			//IL_012b: Unknown result type (might be due to invalid IL or missing references)
			double num = Math.Min(1.0, (DateTime.UtcNow - s).TotalMilliseconds / 560.0);
			double num2 = 1.0 - Math.Pow(1.0 - num, 3.0);
			az = a0 + da * num2;
			el = e2 + (eel - e2) * num2;
			dist = d0 + (edist - d0) * num2;
			target = new Point3D((t0).X + ((etarget).X - (t0).X) * num2, (t0).Y + ((etarget).Y - (t0).Y) * num2, (t0).Z + ((etarget).Z - (t0).Z) * num2);
			UpdateCam();
			if (num >= 1.0)
			{
				CompositionTarget.Rendering -= tick;
				tick = null;
			}
		};
		CompositionTarget.Rendering += tick;
	}

	public void Attach(UIElement host)
	{
		//IL_0021: Unknown result type (might be due to invalid IL or missing references)
		//IL_002b: Expected O, but got Unknown
		//IL_0038: Unknown result type (might be due to invalid IL or missing references)
		//IL_0042: Expected O, but got Unknown
		//IL_004f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0059: Expected O, but got Unknown
		//IL_0066: Unknown result type (might be due to invalid IL or missing references)
		//IL_0070: Expected O, but got Unknown
		host.MouseDown += (MouseButtonEventHandler)delegate(object s, MouseButtonEventArgs e)
		{
			//IL_008c: Unknown result type (might be due to invalid IL or missing references)
			//IL_0092: Invalid comparison between Unknown and I4
			//IL_00a0: Unknown result type (might be due to invalid IL or missing references)
			//IL_00a6: Invalid comparison between Unknown and I4
			//IL_0041: Unknown result type (might be due to invalid IL or missing references)
			//IL_00a9: Unknown result type (might be due to invalid IL or missing references)
			//IL_00af: Invalid comparison between Unknown and I4
			//IL_00c6: Unknown result type (might be due to invalid IL or missing references)
			//IL_00cb: Unknown result type (might be due to invalid IL or missing references)
			//IL_006e: Unknown result type (might be due to invalid IL or missing references)
			//IL_0073: Unknown result type (might be due to invalid IL or missing references)
			if (tick != null)
			{
				CompositionTarget.Rendering -= tick;
				tick = null;
			}
			if (Tool != "" && (int)e.ChangedButton == 0 && HasFit)
			{
				tooling = true;
				toolStart = ((MouseEventArgs)e).GetPosition((IInputElement)(object)host);
				host.CaptureMouse();
			}
			else
			{
				orbiting = (int)e.ChangedButton == 0;
				panning = (int)e.ChangedButton == 2 || (int)e.ChangedButton == 1;
				last = ((MouseEventArgs)e).GetPosition((IInputElement)(object)host);
				host.CaptureMouse();
			}
		};
		host.MouseUp += (MouseButtonEventHandler)delegate(object s, MouseButtonEventArgs e)
		{
			//IL_003a: Unknown result type (might be due to invalid IL or missing references)
			//IL_0046: Unknown result type (might be due to invalid IL or missing references)
			if (tooling)
			{
				tooling = false;
				host.ReleaseMouseCapture();
				this.ToolDrag?.Invoke(toolStart, ((MouseEventArgs)e).GetPosition((IInputElement)(object)host), arg3: true);
			}
			else
			{
				orbiting = (panning = false);
				host.ReleaseMouseCapture();
			}
		};
		host.MouseMove += (MouseEventHandler)delegate(object s, MouseEventArgs e)
		{
			//IL_005d: Unknown result type (might be due to invalid IL or missing references)
			//IL_0062: Unknown result type (might be due to invalid IL or missing references)
			//IL_009b: Unknown result type (might be due to invalid IL or missing references)
			//IL_009c: Unknown result type (might be due to invalid IL or missing references)
			//IL_0023: Unknown result type (might be due to invalid IL or missing references)
			//IL_002f: Unknown result type (might be due to invalid IL or missing references)
			//IL_021a: Unknown result type (might be due to invalid IL or missing references)
			//IL_021f: Unknown result type (might be due to invalid IL or missing references)
			if (tooling)
			{
				this.ToolDrag?.Invoke(toolStart, e.GetPosition((IInputElement)(object)host), arg3: false);
			}
			else if (orbiting || panning)
			{
				Point position = e.GetPosition((IInputElement)(object)host);
				double num = (position).X - (last).X;
				double num2 = (position).Y - (last).Y;
				last = position;
				if (orbiting)
				{
					az -= num * 0.0065;
					el = Math.Max(-1.5707, Math.Min(1.5707, el + num2 * 0.0065));
				}
				else
				{
					double num3 = Math.Cos(el);
					double num4 = Math.Sin(el);
					double num5 = Math.Sin(az);
					double num6 = Math.Cos(az);
					Vector3D val = default(Vector3D);
					val = new Vector3D(num6, 0.0, 0.0 - num5);
					Vector3D val2 = default(Vector3D);
					val2 = new Vector3D((0.0 - num5) * num4, num3, (0.0 - num6) * num4);
					double num7 = dist * 0.0016;
					target = new Point3D((target).X + ((0.0 - (val).X) * num + (val2).X * num2) * num7, (target).Y + ((0.0 - (val).Y) * num + (val2).Y * num2) * num7, (target).Z + ((0.0 - (val).Z) * num + (val2).Z * num2) * num7);
				}
				UpdateCam();
			}
		};
		host.MouseWheel += (MouseWheelEventHandler)delegate(object s, MouseWheelEventArgs e)
		{
			dist = Math.Max(h * 0.5, Math.Min(h * 9.0, dist * ((e.Delta > 0) ? 0.9 : 1.1)));
			UpdateCam();
		};
	}
}

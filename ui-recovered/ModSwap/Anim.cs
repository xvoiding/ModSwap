using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Threading;

namespace ModSwap;

public static class Anim
{
	private static readonly IEasingFunction Out = (IEasingFunction)new CubicEase
	{
		EasingMode = (EasingMode)1
	};

	private static readonly IEasingFunction InOut = (IEasingFunction)new CubicEase
	{
		EasingMode = (EasingMode)2
	};

	public static void Fade(UIElement el, double to, double ms = 260.0)
	{
		//IL_0028: Unknown result type (might be due to invalid IL or missing references)
		//IL_002d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0032: Unknown result type (might be due to invalid IL or missing references)
		//IL_003d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0049: Expected O, but got Unknown
		double opacity = el.Opacity;
		el.BeginAnimation(UIElement.OpacityProperty, (AnimationTimeline)null);
		el.Opacity = to;
		el.BeginAnimation(UIElement.OpacityProperty, (AnimationTimeline)new DoubleAnimation(opacity, to, (Duration)(TimeSpan.FromMilliseconds(ms)))
		{
			EasingFunction = Out,
			FillBehavior = (FillBehavior)1
		});
	}

	private static TranslateTransform Shift(UIElement el)
	{
		//IL_0019: Unknown result type (might be due to invalid IL or missing references)
		//IL_001f: Expected O, but got Unknown
		Transform renderTransform = el.RenderTransform;
		TranslateTransform val = (TranslateTransform)(object)((renderTransform is TranslateTransform) ? renderTransform : null);
		if (val != null && !((Freezable)val).IsFrozen)
		{
			return val;
		}
		return (TranslateTransform)(object)(el.RenderTransform = (Transform)new TranslateTransform());
	}

	public static void In(FrameworkElement el, double ms = 340.0, double dy = 14.0, double delay = 0.0)
	{
		//IL_004d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0052: Unknown result type (might be due to invalid IL or missing references)
		//IL_0057: Unknown result type (might be due to invalid IL or missing references)
		//IL_0062: Unknown result type (might be due to invalid IL or missing references)
		//IL_006e: Unknown result type (might be due to invalid IL or missing references)
		//IL_007a: Expected O, but got Unknown
		//IL_0099: Unknown result type (might be due to invalid IL or missing references)
		//IL_009e: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a3: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ba: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c6: Expected O, but got Unknown
		((UIElement)el).Visibility = (Visibility)0;
		TranslateTransform obj = Shift((UIElement)(object)el);
		((UIElement)el).BeginAnimation(UIElement.OpacityProperty, (AnimationTimeline)null);
		((UIElement)el).Opacity = 1.0;
		TimeSpan value = TimeSpan.FromMilliseconds(delay);
		((UIElement)el).BeginAnimation(UIElement.OpacityProperty, (AnimationTimeline)new DoubleAnimation(0.0, 1.0, (Duration)(TimeSpan.FromMilliseconds(ms)))
		{
			EasingFunction = Out,
			BeginTime = value,
			FillBehavior = (FillBehavior)1
		});
		((Animatable)obj).BeginAnimation(TranslateTransform.YProperty, (AnimationTimeline)new DoubleAnimation(dy, 0.0, (Duration)(TimeSpan.FromMilliseconds(ms + 80.0)))
		{
			EasingFunction = Out,
			BeginTime = value,
			FillBehavior = (FillBehavior)1
		});
	}

	public static void Out_(FrameworkElement el, double ms = 200.0, Action done = null)
	{
		//IL_002e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0033: Unknown result type (might be due to invalid IL or missing references)
		//IL_0038: Unknown result type (might be due to invalid IL or missing references)
		//IL_0044: Expected O, but got Unknown
		DoubleAnimation val = new DoubleAnimation(((UIElement)el).Opacity, 0.0, (Duration)(TimeSpan.FromMilliseconds(ms)))
		{
			EasingFunction = Out
		};
		((Timeline)val).Completed += delegate
		{
			((UIElement)el).BeginAnimation(UIElement.OpacityProperty, (AnimationTimeline)null);
			((UIElement)el).Opacity = 1.0;
			((UIElement)el).Visibility = (Visibility)2;
			done?.Invoke();
		};
		((UIElement)el).BeginAnimation(UIElement.OpacityProperty, (AnimationTimeline)(object)val);
	}

	public static void Brush(SolidColorBrush b, Color to, double ms = 200.0)
	{
		//IL_0006: Unknown result type (might be due to invalid IL or missing references)
		//IL_000d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0012: Unknown result type (might be due to invalid IL or missing references)
		//IL_0017: Unknown result type (might be due to invalid IL or missing references)
		//IL_0027: Expected O, but got Unknown
		((Animatable)b).BeginAnimation(SolidColorBrush.ColorProperty, (AnimationTimeline)new ColorAnimation(to, (Duration)(TimeSpan.FromMilliseconds(ms)))
		{
			EasingFunction = Out
		});
	}

	public static void Count(TextBlock tb, int to, double ms = 700.0)
	{
		//IL_0027: Unknown result type (might be due to invalid IL or missing references)
		//IL_002c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0045: Expected O, but got Unknown
		DateTime s = DateTime.UtcNow;
		DispatcherTimer timer = new DispatcherTimer
		{
			Interval = TimeSpan.FromMilliseconds(16.0)
		};
		timer.Tick += delegate
		{
			double num = Math.Min(1.0, (DateTime.UtcNow - s).TotalMilliseconds / ms);
			double num2 = 1.0 - Math.Pow(1.0 - num, 3.0);
			tb.Text = ((int)Math.Round((double)to * num2)).ToString("N0");
			if (num >= 1.0)
			{
				timer.Stop();
			}
		};
		timer.Start();
	}

	public static void Sweep(TranslateTransform t, double from, double to, double ms)
	{
		//IL_000e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0013: Unknown result type (might be due to invalid IL or missing references)
		//IL_0018: Unknown result type (might be due to invalid IL or missing references)
		//IL_0019: Unknown result type (might be due to invalid IL or missing references)
		//IL_0023: Unknown result type (might be due to invalid IL or missing references)
		//IL_0033: Expected O, but got Unknown
		((Animatable)t).BeginAnimation(TranslateTransform.XProperty, (AnimationTimeline)new DoubleAnimation(from, to, (Duration)(TimeSpan.FromMilliseconds(ms)))
		{
			RepeatBehavior = RepeatBehavior.Forever,
			EasingFunction = InOut
		});
	}
}

using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;

namespace QuantDataGatewayDesktop
{
    internal static class LauncherRuntime
    {
        internal const int DefaultPort = 8001;
        internal const string MutexName = "Local\\QuantDataGatewayV328DesktopLauncher";
        private static readonly object LogLock = new object();

        internal static string FindProjectRoot()
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string current = Environment.CurrentDirectory;
            string[] candidates = new string[]
            {
                baseDir,
                Directory.GetParent(baseDir.TrimEnd(Path.DirectorySeparatorChar)) == null
                    ? baseDir
                    : Directory.GetParent(baseDir.TrimEnd(Path.DirectorySeparatorChar)).FullName,
                current
            };
            foreach (string candidate in candidates)
            {
                if (File.Exists(Path.Combine(candidate, "quant_data", "api.py")))
                    return Path.GetFullPath(candidate);
            }
            return Path.GetFullPath(baseDir);
        }

        internal static string PythonPath(string root)
        {
            return Path.Combine(root, ".venv", "Scripts", "python.exe");
        }

        internal static string StatePath(string root)
        {
            return Path.Combine(root, "data", "launcher-state.json");
        }

        internal static string LogPath(string root)
        {
            return Path.Combine(root, "logs", "desktop-launcher.log");
        }

        internal static int PortFromArgs(string[] args)
        {
            foreach (string arg in args)
            {
                if (arg.StartsWith("--port=", StringComparison.OrdinalIgnoreCase))
                {
                    int parsed;
                    if (Int32.TryParse(arg.Substring(7), out parsed) && parsed > 0 && parsed < 65536)
                        return parsed;
                }
            }
            int envPort;
            if (Int32.TryParse(Environment.GetEnvironmentVariable("QDG_PORT"), out envPort) && envPort > 0 && envPort < 65536)
                return envPort;
            return DefaultPort;
        }

        internal static bool HasArg(string[] args, string expected)
        {
            foreach (string arg in args)
                if (String.Equals(arg, expected, StringComparison.OrdinalIgnoreCase))
                    return true;
            return false;
        }

        internal static int ReadStateInt(string root, string key, int fallback)
        {
            try
            {
                string text = File.ReadAllText(StatePath(root), Encoding.UTF8);
                Match match = Regex.Match(text, "\\\"" + Regex.Escape(key) + "\\\"\\s*:\\s*(\\d+)");
                int value;
                if (match.Success && Int32.TryParse(match.Groups[1].Value, out value))
                    return value;
            }
            catch { }
            return fallback;
        }

        internal static void WriteState(string root, int port, int pid)
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(StatePath(root)));
                string payload = "{\n" +
                    "  \"port\": " + port + ",\n" +
                    "  \"pid\": " + pid + ",\n" +
                    "  \"project_root\": \"" + JsonEscape(root) + "\",\n" +
                    "  \"started_at\": \"" + DateTime.Now.ToString("yyyy-MM-ddTHH:mm:ss") + "\"\n" +
                    "}\n";
                File.WriteAllText(StatePath(root), payload, new UTF8Encoding(false));
            }
            catch { }
        }

        internal static void ClearState(string root, int expectedPid)
        {
            try
            {
                int statePid = ReadStateInt(root, "pid", 0);
                if (expectedPid <= 0 || statePid == expectedPid)
                    File.Delete(StatePath(root));
            }
            catch { }
        }

        private static string JsonEscape(string value)
        {
            return (value ?? "").Replace("\\", "\\\\").Replace("\"", "\\\"");
        }

        internal static void AppendLog(string root, string message)
        {
            try
            {
                lock (LogLock)
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(LogPath(root)));
                    File.AppendAllText(
                        LogPath(root),
                        DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + " " + message + Environment.NewLine,
                        new UTF8Encoding(false)
                    );
                }
            }
            catch { }
        }

        internal static string DashboardUrl(int port)
        {
            return "http://127.0.0.1:" + port + "/auto-trading";
        }

        internal static bool IsGatewayReady(int port)
        {
            try
            {
                HttpWebRequest request = (HttpWebRequest)WebRequest.Create(DashboardUrl(port));
                request.Method = "GET";
                request.Timeout = 1400;
                request.ReadWriteTimeout = 1400;
                request.Proxy = null;
                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                using (Stream stream = response.GetResponseStream())
                using (StreamReader reader = new StreamReader(stream, Encoding.UTF8))
                {
                    string body = reader.ReadToEnd();
                    return response.StatusCode == HttpStatusCode.OK && body.Contains("workspaceFrame");
                }
            }
            catch { return false; }
        }

        internal static bool IsPortAvailable(int port)
        {
            TcpListener listener = null;
            try
            {
                listener = new TcpListener(IPAddress.Loopback, port);
                listener.Start();
                return true;
            }
            catch { return false; }
            finally { if (listener != null) listener.Stop(); }
        }

        internal static int SelectPort(int preferred)
        {
            if (IsGatewayReady(preferred) || IsPortAvailable(preferred))
                return preferred;
            for (int port = preferred + 1; port <= Math.Min(65535, preferred + 30); port++)
                if (IsGatewayReady(port) || IsPortAvailable(port))
                    return port;
            return preferred;
        }

        internal static void OpenBrowser(int port)
        {
            string url = DashboardUrl(port);
            try
            {
                ProcessStartInfo info = new ProcessStartInfo("cmd.exe", "/c start \"\" \"" + url + "\"");
                info.CreateNoWindow = true;
                info.UseShellExecute = false;
                Process.Start(info);
            }
            catch { }
        }

        internal static Process StartServer(string root, int port)
        {
            string python = PythonPath(root);
            if (!File.Exists(python))
                throw new FileNotFoundException("Missing project Python runtime", python);
            ProcessStartInfo info = new ProcessStartInfo();
            info.FileName = python;
            info.Arguments = "-m uvicorn quant_data.api:app --host 127.0.0.1 --port " + port + " --log-level warning --no-access-log";
            info.WorkingDirectory = root;
            info.UseShellExecute = false;
            info.CreateNoWindow = true;
            info.RedirectStandardOutput = true;
            info.RedirectStandardError = true;
            info.EnvironmentVariables["PYTHONUTF8"] = "1";
            info.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
            info.EnvironmentVariables["QDG_DESKTOP_LAUNCHER"] = "1";
            info.EnvironmentVariables["QDG_PORT"] = port.ToString();
            Process process = new Process();
            process.StartInfo = info;
            process.EnableRaisingEvents = true;
            process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e)
            {
                if (!String.IsNullOrWhiteSpace(e.Data)) AppendLog(root, "OUT " + e.Data);
            };
            process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e)
            {
                if (!String.IsNullOrWhiteSpace(e.Data)) AppendLog(root, "ERR " + e.Data);
            };
            if (!process.Start())
                throw new InvalidOperationException("Unable to start the service process");
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            return process;
        }

        internal static bool StopStateProcess(string root)
        {
            int pid = ReadStateInt(root, "pid", 0);
            if (pid <= 0) return false;
            try
            {
                Process process = Process.GetProcessById(pid);
                process.Kill();
                process.WaitForExit(5000);
                ClearState(root, pid);
                return true;
            }
            catch
            {
                ClearState(root, pid);
                return false;
            }
        }
    }

    internal sealed class LauncherForm : Form
    {
        private readonly string root;
        private readonly bool noBrowser;
        private int port;
        private Process server;
        private bool ownsServer;
        private readonly Label statusLabel;
        private readonly Label detailLabel;
        private readonly Button openButton;
        private readonly Button stopButton;

        internal LauncherForm(string rootPath, int requestedPort, bool suppressBrowser)
        {
            root = rootPath;
            port = requestedPort;
            noBrowser = suppressBrowser;
            Text = "Quant Data Gateway";
            StartPosition = FormStartPosition.CenterScreen;
            Size = new Size(620, 280);
            MinimumSize = new Size(540, 250);
            BackColor = Color.FromArgb(8, 17, 31);
            ForeColor = Color.FromArgb(231, 240, 255);
            Font = new Font("Microsoft YaHei UI", 10F, FontStyle.Regular);

            Label title = new Label();
            title.Text = "\u91cf\u5316\u6570\u636e\u7f51\u5173";
            title.Font = new Font("Microsoft YaHei UI", 18F, FontStyle.Bold);
            title.ForeColor = Color.FromArgb(191, 219, 254);
            title.Location = new Point(26, 22);
            title.AutoSize = true;
            Controls.Add(title);

            Label subtitle = new Label();
            subtitle.Text = "\u552f\u4e00\u542f\u52a8\u5165\u53e3  |  \u81ea\u52a8\u4ea4\u6613\u603b\u63a7\u53f0";
            subtitle.ForeColor = Color.FromArgb(145, 166, 197);
            subtitle.Location = new Point(29, 65);
            subtitle.AutoSize = true;
            Controls.Add(subtitle);

            Panel statusPanel = new Panel();
            statusPanel.Location = new Point(28, 100);
            statusPanel.Size = new Size(548, 62);
            statusPanel.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            statusPanel.BackColor = Color.FromArgb(16, 26, 44);
            Controls.Add(statusPanel);

            statusLabel = new Label();
            statusLabel.Text = "\u6b63\u5728\u68c0\u67e5\u672c\u5730\u670d\u52a1...";
            statusLabel.Font = new Font("Microsoft YaHei UI", 11F, FontStyle.Bold);
            statusLabel.ForeColor = Color.FromArgb(253, 230, 138);
            statusLabel.Location = new Point(14, 10);
            statusLabel.AutoSize = true;
            statusPanel.Controls.Add(statusLabel);

            detailLabel = new Label();
            detailLabel.Text = root;
            detailLabel.ForeColor = Color.FromArgb(145, 166, 197);
            detailLabel.Location = new Point(14, 34);
            detailLabel.AutoEllipsis = true;
            detailLabel.Size = new Size(516, 20);
            detailLabel.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            statusPanel.Controls.Add(detailLabel);

            openButton = MakeButton("\u6253\u5f00\u603b\u63a7\u53f0", 28, 184, Color.FromArgb(37, 99, 235));
            openButton.Enabled = false;
            openButton.Click += delegate { LauncherRuntime.OpenBrowser(port); };
            Controls.Add(openButton);

            stopButton = MakeButton("\u505c\u6b62\u670d\u52a1", 190, 184, Color.FromArgb(153, 27, 27));
            stopButton.Enabled = false;
            stopButton.Click += delegate { StopService(true); };
            Controls.Add(stopButton);

            Button exitButton = MakeButton("\u9000\u51fa", 352, 184, Color.FromArgb(37, 55, 85));
            exitButton.Click += delegate { Close(); };
            Controls.Add(exitButton);

            Shown += delegate { StartWorker(); };
            FormClosing += delegate { StopService(false); };
        }

        private Button MakeButton(string text, int x, int y, Color color)
        {
            Button button = new Button();
            button.Text = text;
            button.Location = new Point(x, y);
            button.Size = new Size(144, 38);
            button.FlatStyle = FlatStyle.Flat;
            button.FlatAppearance.BorderSize = 0;
            button.BackColor = color;
            button.ForeColor = Color.White;
            button.Font = new Font("Microsoft YaHei UI", 10F, FontStyle.Bold);
            return button;
        }

        private void StartWorker()
        {
            Thread worker = new Thread(delegate()
            {
                try
                {
                    int savedPort = LauncherRuntime.ReadStateInt(root, "port", port);
                    if (LauncherRuntime.IsGatewayReady(savedPort))
                    {
                        port = savedPort;
                        SetReady("\u670d\u52a1\u5df2\u8fd0\u884c", false);
                        return;
                    }
                    port = LauncherRuntime.SelectPort(port);
                    SetStatus("\u6b63\u5728\u542f\u52a8\u670d\u52a1...", "127.0.0.1:" + port, Color.FromArgb(253, 230, 138));
                    server = LauncherRuntime.StartServer(root, port);
                    ownsServer = true;
                    LauncherRuntime.WriteState(root, port, server.Id);
                    DateTime deadline = DateTime.Now.AddSeconds(120);
                    while (DateTime.Now < deadline)
                    {
                        if (server.HasExited)
                            throw new InvalidOperationException("Service exited with code " + server.ExitCode);
                        if (LauncherRuntime.IsGatewayReady(port))
                        {
                            SetReady("\u670d\u52a1\u5df2\u5c31\u7eea", true);
                            return;
                        }
                        Thread.Sleep(500);
                    }
                    throw new TimeoutException("Service startup timed out");
                }
                catch (Exception error)
                {
                    LauncherRuntime.AppendLog(root, "LAUNCH " + error);
                    SetStatus(
                        "\u542f\u52a8\u5931\u8d25",
                        "\u8bf7\u67e5\u770b " + LauncherRuntime.LogPath(root),
                        Color.FromArgb(252, 165, 165)
                    );
                }
            });
            worker.IsBackground = true;
            worker.Start();
        }

        private void SetReady(string message, bool managed)
        {
            if (InvokeRequired)
            {
                BeginInvoke(new Action<string, bool>(SetReady), message, managed);
                return;
            }
            ownsServer = managed;
            statusLabel.Text = message;
            statusLabel.ForeColor = Color.FromArgb(134, 239, 172);
            detailLabel.Text = LauncherRuntime.DashboardUrl(port);
            openButton.Enabled = true;
            stopButton.Enabled = managed;
            if (!noBrowser) LauncherRuntime.OpenBrowser(port);
        }

        private void SetStatus(string message, string detail, Color color)
        {
            if (InvokeRequired)
            {
                BeginInvoke(new Action<string, string, Color>(SetStatus), message, detail, color);
                return;
            }
            statusLabel.Text = message;
            statusLabel.ForeColor = color;
            detailLabel.Text = detail;
        }

        private void StopService(bool updateUi)
        {
            try
            {
                if (ownsServer && server != null && !server.HasExited)
                {
                    int pid = server.Id;
                    server.Kill();
                    server.WaitForExit(5000);
                    LauncherRuntime.ClearState(root, pid);
                }
            }
            catch (Exception error)
            {
                LauncherRuntime.AppendLog(root, "STOP " + error.Message);
            }
            finally
            {
                ownsServer = false;
                if (updateUi)
                {
                    stopButton.Enabled = false;
                    openButton.Enabled = false;
                    SetStatus("\u670d\u52a1\u5df2\u505c\u6b62", root, Color.FromArgb(253, 230, 138));
                }
            }
        }
    }

    internal static class Program
    {
        [STAThread]
        private static void Main(string[] args)
        {
            string root = LauncherRuntime.FindProjectRoot();
            if (LauncherRuntime.HasArg(args, "--stop"))
            {
                LauncherRuntime.StopStateProcess(root);
                return;
            }

            bool created;
            using (Mutex mutex = new Mutex(true, LauncherRuntime.MutexName, out created))
            {
                if (!created)
                {
                    int runningPort = LauncherRuntime.ReadStateInt(root, "port", LauncherRuntime.PortFromArgs(args));
                    if (!LauncherRuntime.HasArg(args, "--no-browser") && LauncherRuntime.IsGatewayReady(runningPort))
                        LauncherRuntime.OpenBrowser(runningPort);
                    return;
                }
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new LauncherForm(
                    root,
                    LauncherRuntime.PortFromArgs(args),
                    LauncherRuntime.HasArg(args, "--no-browser")
                ));
            }
        }
    }
}

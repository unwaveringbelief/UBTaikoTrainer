<div align="center">
<h1>🥁 U.B. Taiko Pattern Trainer</h1>
<p>A dedicated, lightweight training tool designed for <strong>Taiko no Tatsujin</strong> players.</p>
<p><em>Focus on drilling complex patterns, improving stream consistency, and refining rhythm accuracy with arcade-strict timing windows.</em></p>
</div>

<h2>✨ Why did I make it?</h2>

Standard simulators are great for playing songs, but they aren't optimized for drilling specific rudiments. I wanted a way to:

Isolate patterns: Practice triplets, DDK, or long streams repeatedly.

Strict Timing: Feedback is based on official Arcade windows (Perfect: 25ms).

Measure Accuracy: A real-time graph shows if you are hitting Early or Late.

Improve Sight-Reading: Use the Auto-Randomize feature for infinite reading exercises.

<h2>🎮 Features</h2>

Visualizer Mode: Interactive metronome for checking audio sync or warming up.

Game Mode: Full training experience with scoring, combo tracking, and accuracy stats.

Demo Play: Let the CPU play the pattern perfectly to internalize the rhythm.

Dynamic Sequencer: 32-step editor to draw your own custom patterns.

Preset Library: Built-in common rudiments (Streams, Triplets, Alt-sticking).

Coach Mode: Get analysis and tips (e.g., "Hitting Early -> Adjust Offset").

<h2>📥 Download & Installation</h2>

Windows Executable (Easiest)

Go to the <a href="https://github.com/unwaveringbelief/UBTaikoTrainer/releases">Releases</a> page.

Download the <code>TaikoTrainer.zip</code> file.

Extract the folder and run <code>TaikoTrainer.exe</code>.

No Python installation required!

Run from Source (Python)

Install <a href="https://www.python.org/downloads/windows/">Python 3.x.</a>

Clone this repository:

<pre><code>git clone https://github.com/unwaveringbelief/UBTaikoTrainer.git</pre></code>


Install dependencies:

<pre><code>pip install pygame</pre></code>


Run the trainer:

<pre><code>python main.py</code></pre>


<h2>🛠️ Controls</h2>
<table>
  <thead>
    <tr>
      <th align="left">Action</th>
      <th align="center">Default Key </th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Left / Right DON</strong></td>
      <td align="center"><kbd>F</kbd> / <kbd>J</kbd></td>
    </tr>
    <tr>
      <td><strong>Left / Right KA</strong></td>
      <td align="center"><kbd>D</kbd> / <kbd>K</kbd></td>
    </tr>
    <tr>
      <td><strong>Start / Stop</strong></td>
      <td align="center"><kbd>Space</kbd></td>
    </tr>
    <tr>
      <td><strong>BPM Up / Down</strong> (±5 BPM)</td>
      <td align="center"><kbd>←</kbd> / <kbd>→</kbd></td>
    </tr>
    <tr>
      <td><strong>Fullscreen</strong></td>
      <td align="center"><kbd>F11</kbd></td>
    </tr>
  </tbody>
</table>


<h2>🛡️ Security & Antivirus Note</h2>

Since this is an independent, non-signed open-source project, Windows SmartScreen or some Antivirus software might flag the executable as "Unknown" or "Suspicious".

This is a False Positive.

Why? The app is compiled using PyInstaller, which is often flagged by heuristic engines because it extracts files to a temporary folder.

Verification: You can check the source code yourself here on GitHub to verify the logic.

Solution: Click "More info" and "Run anyway" if prompted by Windows.

<h2>⚖️ Disclaimer & Non-Affiliation</h2>

This is an unofficial, non-commercial fan project. "Taiko no Tatsujin" and related trademarks are the property of Bandai Namco Entertainment Inc.

This software is provided for educational and training purposes only. It does not distribute any copyrighted audio, visual assets, or charts from the original games.

<h2>📝 License</h2>

This project is open-source. Happy drumming! 🔴🔵

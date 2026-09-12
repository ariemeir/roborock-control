
import SwiftUI
import AVKit

// <-- put your Mac's Wi-Fi IP here
let serverBase = "http://YOUR-SERVER-HOST:8050"   // e.g. a tailnet name or LAN IP

struct Robot: Identifiable, Decodable {
    let name: String
    var id: String { name }
}

func enc(_ s: String) -> String {
    s.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? s
}

func post(_ path: String) async {
    guard let url = URL(string: serverBase + path) else { return }
    var req = URLRequest(url: url); req.httpMethod = "POST"
    _ = try? await URLSession.shared.data(for: req)
}

struct ContentView: View {
    @State private var robots: [Robot] = []
    @State private var error: String?

    var body: some View {
        NavigationStack {
            List {
                if let error { Text(error).foregroundStyle(.red) }
                ForEach(robots) { r in
                    NavigationLink(r.name) { ControlView(device: r.name) }
                }
            }
            .navigationTitle("My Roborocks")
            .task { await load() }
            .refreshable { await load() }
        }
    }

    func load() async {
        guard let url = URL(string: serverBase + "/devices") else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            robots = try JSONDecoder().decode([Robot].self, from: data)
            error = nil
        } catch {
            self.error = "Can't reach the Mac. Is server.py running and the IP right?"
        }
    }
}

struct ControlView: View {
    let device: String
    @State private var videoOn = false
    @State private var player: AVPlayer?

    var body: some View {
        ScrollView {
            VStack(spacing: 22) {
                videoSection
                pad("arrow.up") { await move("forward") }
                HStack(spacing: 22) {
                    pad("arrow.left") { await move("left") }
                    pad("stop.fill") { await move("stop") }
                    pad("arrow.right") { await move("right") }
                }
                pad("arrow.down") { await move("back") }
                HStack(spacing: 16) {
                    action("Find", "speaker.wave.2.fill") { await cmd("/find") }
                    action("Dock", "house.fill") { await cmd("/dock") }
                }.padding(.top, 12)
            }
            .padding()
        }
        .navigationTitle(device)
        .navigationBarTitleDisplayMode(.inline)
        .task { await post("/rc/start?device=\(enc(device))") }
        .onDisappear {
            Task { await post("/rc/end?device=\(enc(device))"); await stopVideo() }
        }
    }

    var videoSection: some View {
        VStack(spacing: 10) {
            if let player {
                VideoPlayer(player: player)
                    .frame(height: 220)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            Toggle("Live video", isOn: $videoOn)
                .onChange(of: videoOn) { _, on in
                    Task { on ? await startVideo() : await stopVideo() }
                }
        }
    }

    func startVideo() async {
        await post("/video/start")
        try? await Task.sleep(nanoseconds: 2_500_000_000)   // let ffmpeg build segments
        guard let url = URL(string: serverBase + "/hls/stream.m3u8") else { return }
        let p = AVPlayer(url: url)
        p.play()
        player = p
    }

    func stopVideo() async {
        player?.pause()
        player = nil
        await post("/video/stop")
    }

    func move(_ d: String) async { await post("/rc/move?device=\(enc(device))&dir=\(d)") }
    func cmd(_ p: String) async { await post("\(p)?device=\(enc(device))") }

    func pad(_ symbol: String, _ act: @escaping () async -> Void) -> some View {
        Button { Task { await act() } } label: {
            Image(systemName: symbol)
                .font(.system(size: 34, weight: .semibold))
                .frame(width: 84, height: 84)
                .background(.tint.opacity(0.15))
                .clipShape(RoundedRectangle(cornerRadius: 18))
        }
    }

    func action(_ title: String, _ symbol: String, _ act: @escaping () async -> Void) -> some View {
        Button { Task { await act() } } label: {
            Label(title, systemImage: symbol)
                .font(.headline).frame(maxWidth: .infinity).padding()
                .background(.tint.opacity(0.15))
                .clipShape(RoundedRectangle(cornerRadius: 14))
        }
    }
}

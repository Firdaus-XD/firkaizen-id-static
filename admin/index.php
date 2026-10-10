<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Admin Dashboard — FirKaizen Material & Konstruksi</title>
  <link rel="icon" type="image/png" href="https://firkaizen.com/logo.png"/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet"/>
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            'fk-navy': '#070E33',
            'fk-dark': '#0B1650',
            'fk-blue': '#0B6BFF',
            'fk-surface': '#F8FAFC',
            'fk-border': '#E2E8F0',
            'fk-heading': '#0F172A',
            'fk-body': '#475569',
            'fk-green': '#16A34A',
            'fk-amber': '#F59E0B'
          },
          fontFamily: {
            sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
            display: ['Space Grotesk', 'sans-serif']
          }
        }
      }
    };
  </script>
</head>
<body class="bg-slate-100 font-sans text-fk-body antialiased min-h-screen">

  <!-- LOGIN CONTAINER (SHOWN IF NOT LOGGED IN) -->
  <div id="loginSection" class="min-h-screen flex items-center justify-center p-5">
    <div class="bg-white max-w-md w-full p-8 rounded-3xl border border-fk-border shadow-xl space-y-6">
      <div class="text-center space-y-2">
        <img src="https://firkaizen.com/logo.png" alt="Logo" class="h-12 w-12 mx-auto object-contain"/>
        <h1 class="text-xl font-bold font-display text-fk-heading">Admin FirKaizen Material</h1>
        <p class="text-xs text-fk-body">Masuk untuk mengelola prospek, katalog harga, &amp; data supplier</p>
      </div>

      <form onsubmit="handleLogin(event)" class="space-y-4">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-fk-heading mb-1.5">Password Admin</label>
          <input id="loginPassword" type="password" required placeholder="Masukkan password..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-4 py-3 text-sm text-fk-heading focus:outline-none focus:border-fk-blue focus:bg-white transition-all"/>
        </div>
        <div id="loginError" class="text-xs text-rose-500 font-medium hidden"></div>
        <button type="submit" id="loginBtn" class="w-full bg-fk-blue hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-xl text-sm shadow-md transition-all">
          Masuk ke Dashboard
        </button>
      </form>
    </div>
  </div>

  <!-- DASHBOARD CONTAINER (SHOWN IF LOGGED IN) -->
  <div id="dashSection" class="hidden min-h-screen flex flex-col">
    <!-- Navbar -->
    <header class="bg-white border-b border-fk-border sticky top-0 z-40">
      <div class="max-w-7xl mx-auto px-5 sm:px-8 h-16 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <img src="https://firkaizen.com/logo.png" alt="Logo" class="h-8 w-8 object-contain"/>
          <div>
            <div class="font-display font-bold text-base text-fk-heading leading-tight">FirKaizen Material Admin</div>
            <div class="text-[10px] text-fk-body font-semibold uppercase tracking-wider">PT FirKaizen Digital Solutions</div>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <a href="/" target="_blank" class="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border border-fk-border text-fk-heading hover:bg-slate-50">
            <span class="material-symbols-outlined text-[16px]">visibility</span>
            <span>Lihat Website</span>
          </a>
          <button onclick="handleLogout()" type="button" class="inline-flex items-center gap-1.5 text-xs font-bold text-rose-600 bg-rose-50 hover:bg-rose-100 px-3 py-1.5 rounded-lg border border-rose-200 transition-colors">
            <span class="material-symbols-outlined text-[16px]">logout</span>
            <span>Keluar</span>
          </button>
        </div>
      </div>
    </header>

    <!-- Content Area -->
    <div class="max-w-7xl mx-auto px-5 sm:px-8 py-8 w-full flex-1 space-y-6">

      <!-- Metrics Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div class="bg-white p-5 rounded-2xl border border-fk-border shadow-xs">
          <div class="text-[11px] font-bold uppercase tracking-wider text-fk-body">Total Semua Prospek</div>
          <div id="statTotalLeads" class="text-2xl sm:text-3xl font-extrabold text-fk-heading mt-1 font-display">0</div>
          <div class="text-[11px] text-slate-500 mt-1">Akumulasi kontak masuk</div>
        </div>
        <div class="bg-white p-5 rounded-2xl border border-blue-200 bg-blue-50/30 shadow-xs">
          <div class="text-[11px] font-bold uppercase tracking-wider text-fk-blue">Prospek Baru (Follow-Up)</div>
          <div id="statNewLeads" class="text-2xl sm:text-3xl font-extrabold text-fk-blue mt-1 font-display">0</div>
          <div class="text-[11px] text-fk-blue/80 mt-1">Perlu segera dihubungi</div>
        </div>
        <div class="bg-white p-5 rounded-2xl border border-emerald-200 bg-emerald-50/30 shadow-xs">
          <div class="text-[11px] font-bold uppercase tracking-wider text-emerald-700">Closing / Deal Proyek</div>
          <div id="statDealLeads" class="text-2xl sm:text-3xl font-extrabold text-emerald-600 mt-1 font-display">0</div>
          <div class="text-[11px] text-emerald-700/80 mt-1">Pengerjaan &amp; Pengiriman</div>
        </div>
        <div class="bg-white p-5 rounded-2xl border border-fk-border shadow-xs">
          <div class="text-[11px] font-bold uppercase tracking-wider text-fk-body">Estimasi Nilai Prospek</div>
          <div id="statValuation" class="text-2xl sm:text-3xl font-extrabold text-fk-heading mt-1 font-display">Rp 0</div>
          <div class="text-[11px] text-slate-500 mt-1">Tahap survey / penawaran</div>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex items-center gap-2 border-b border-fk-border pb-2 overflow-x-auto">
        <button onclick="setTab('leads')" id="tabBtn-leads" class="px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-fk-heading text-white transition-colors">
          📋 Manajemen Prospek (Leads)
        </button>
        <button onclick="setTab('products')" id="tabBtn-products" class="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-fk-body hover:bg-slate-200 transition-colors">
          🏷️ Katalog &amp; Harga Produk
        </button>
        <button onclick="setTab('suppliers')" id="tabBtn-suppliers" class="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-fk-body hover:bg-slate-200 transition-colors">
          🏭 Data Supplier &amp; Rekanan
        </button>
        <button onclick="setTab('settings')" id="tabBtn-settings" class="px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-fk-body hover:bg-slate-200 transition-colors">
          ⚙️ Pengaturan &amp; WhatsApp
        </button>
      </div>

      <!-- TAB 1: LEADS MANAGEMENT -->
      <div id="tab-leads" class="space-y-4">
        <div class="bg-white p-5 rounded-2xl border border-fk-border shadow-xs flex flex-wrap items-center justify-between gap-4">
          <div class="flex flex-wrap items-center gap-2">
            <select id="filterDivision" onchange="loadLeads()" class="bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs font-semibold text-fk-heading">
              <option value="">Semua Divisi</option>
              <option value="paving">Paving Block</option>
              <option value="genteng">Genteng Pres</option>
              <option value="gapura">Jasa Gapura</option>
              <option value="renovasi">Renovasi Rumah</option>
            </select>
            <select id="filterStatus" onchange="loadLeads()" class="bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs font-semibold text-fk-heading">
              <option value="">Semua Status</option>
              <option value="BARU">BARU</option>
              <option value="SURVEY">SURVEY</option>
              <option value="PENAWARAN">PENAWARAN</option>
              <option value="DEAL">DEAL</option>
              <option value="SELESAI">SELESAI</option>
              <option value="BATAL">BATAL</option>
            </select>
            <button onclick="loadLeads()" type="button" class="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-xs font-bold text-fk-heading">
              Refresh
            </button>
          </div>

          <div class="text-xs text-fk-body" id="leadsCountLabel">Memuat data...</div>
        </div>

        <div class="bg-white rounded-2xl border border-fk-border shadow-xs overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs border-collapse min-w-[700px]">
              <thead class="bg-slate-50 border-b border-fk-border text-fk-heading font-bold uppercase tracking-wider">
                <tr>
                  <th class="p-3.5">Tanggal</th>
                  <th class="p-3.5">Nama &amp; WhatsApp</th>
                  <th class="p-3.5">Divisi</th>
                  <th class="p-3.5">Volume / Luas</th>
                  <th class="p-3.5">Lokasi</th>
                  <th class="p-3.5">Status Prospek</th>
                  <th class="p-3.5">Aksi</th>
                </tr>
              </thead>
              <tbody id="leadsTableBody" class="divide-y divide-fk-border">
                <tr><td colspan="7" class="p-5 text-center text-slate-400">Memuat data prospek...</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- TAB 2: PRODUCTS CATALOG -->
      <div id="tab-products" class="hidden space-y-4">
        <div class="bg-white p-5 rounded-2xl border border-fk-border shadow-xs flex items-center justify-between gap-4">
          <div>
            <h3 class="text-base font-bold text-fk-heading font-display">Katalog Harga &amp; Satuan</h3>
            <p class="text-xs text-fk-body">Kelola daftar harga satuan material dan jasa borongan per divisi</p>
          </div>
          <button onclick="openProductModal()" class="px-4 py-2.5 rounded-xl bg-fk-blue hover:bg-blue-700 text-white font-bold text-xs shadow-sm flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">add</span>
            <span>Tambah Produk</span>
          </button>
        </div>

        <div class="bg-white rounded-2xl border border-fk-border shadow-xs overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs border-collapse min-w-[600px]">
              <thead class="bg-slate-50 border-b border-fk-border text-fk-heading font-bold uppercase tracking-wider">
                <tr>
                  <th class="p-3.5">Divisi</th>
                  <th class="p-3.5">Nama Produk / Jasa</th>
                  <th class="p-3.5">Spesifikasi</th>
                  <th class="p-3.5">Satuan</th>
                  <th class="p-3.5">Harga</th>
                  <th class="p-3.5">Aksi</th>
                </tr>
              </thead>
              <tbody id="productsTableBody" class="divide-y divide-fk-border">
                <!-- Loaded via JS -->
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- TAB 3: SUPPLIERS DIRECTORY -->
      <div id="tab-suppliers" class="hidden space-y-4">
        <div class="bg-white p-5 rounded-2xl border border-fk-border shadow-xs flex items-center justify-between gap-4">
          <div>
            <h3 class="text-base font-bold text-fk-heading font-display">Direktori Supplier &amp; Mandor Rekanan</h3>
            <p class="text-xs text-rose-600 font-semibold">🔒 Data rahasia internal: catatan harga modal (HPP) &amp; nomor telepon langsung produsen</p>
          </div>
          <button onclick="openSupplierModal()" class="px-4 py-2.5 rounded-xl bg-fk-blue hover:bg-blue-700 text-white font-bold text-xs shadow-sm flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">add</span>
            <span>Tambah Supplier</span>
          </button>
        </div>

        <div class="bg-white rounded-2xl border border-fk-border shadow-xs overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs border-collapse min-w-[700px]">
              <thead class="bg-slate-50 border-b border-fk-border text-fk-heading font-bold uppercase tracking-wider">
                <tr>
                  <th class="p-3.5">Divisi</th>
                  <th class="p-3.5">Nama Supplier / Pabrik</th>
                  <th class="p-3.5">PIC &amp; WhatsApp</th>
                  <th class="p-3.5">Lokasi Pabrik / Gudang</th>
                  <th class="p-3.5">Catatan HPP / Modal</th>
                  <th class="p-3.5">Aksi</th>
                </tr>
              </thead>
              <tbody id="suppliersTableBody" class="divide-y divide-fk-border">
                <!-- Loaded via JS -->
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- TAB 4: SETTINGS & WA DISPATCH -->
      <div id="tab-settings" class="hidden space-y-6">
        <div class="bg-white p-7 rounded-2xl border border-fk-border shadow-xs max-w-2xl">
          <h3 class="text-base font-bold text-fk-heading font-display mb-1">Routing Nomor WhatsApp per Divisi</h3>
          <p class="text-xs text-fk-body mb-6">Tentukan nomor WhatsApp tujuan ketika calon pembeli menekan tombol konsultasi dari masing-masing divisi.</p>

          <form onsubmit="handleSaveSettings(event)" class="space-y-4">
            <div>
              <label class="block text-xs font-bold uppercase tracking-wider text-fk-heading mb-1">WA Divisi Paving Block</label>
              <input id="set_wa_paving" type="text" placeholder="628..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-4 py-2.5 text-xs text-fk-heading"/>
            </div>
            <div>
              <label class="block text-xs font-bold uppercase tracking-wider text-fk-heading mb-1">WA Divisi Genteng Pres</label>
              <input id="set_wa_genteng" type="text" placeholder="628..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-4 py-2.5 text-xs text-fk-heading"/>
            </div>
            <div>
              <label class="block text-xs font-bold uppercase tracking-wider text-fk-heading mb-1">WA Divisi Jasa Gapura</label>
              <input id="set_wa_gapura" type="text" placeholder="628..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-4 py-2.5 text-xs text-fk-heading"/>
            </div>
            <div>
              <label class="block text-xs font-bold uppercase tracking-wider text-fk-heading mb-1">WA Divisi Renovasi Rumah</label>
              <input id="set_wa_renovasi" type="text" placeholder="628..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-4 py-2.5 text-xs text-fk-heading"/>
            </div>

            <div class="pt-4 border-t border-fk-border">
              <label class="block text-xs font-bold uppercase tracking-wider text-fk-heading mb-1">Ubah Password Admin (Kosongkan jika tidak diganti)</label>
              <input id="set_new_password" type="password" placeholder="Password baru..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-4 py-2.5 text-xs text-fk-heading"/>
            </div>

            <div class="pt-2">
              <button type="submit" class="bg-fk-blue hover:bg-blue-700 text-white font-bold py-2.5 px-5 rounded-xl text-xs shadow-sm transition-all">
                Simpan Pengaturan
              </button>
            </div>
            <div id="settingsMsg" class="text-xs font-semibold text-emerald-600 hidden"></div>
          </form>
        </div>
      </div>

    </div>
  </div>

  <!-- MODAL PRODUK -->
  <div id="productModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 hidden">
    <div class="bg-white max-w-md w-full p-6 rounded-3xl border border-fk-border shadow-xl space-y-4">
      <h3 class="text-base font-bold text-fk-heading font-display" id="productModalTitle">Tambah Produk Baru</h3>
      <form onsubmit="handleSaveProduct(event)" class="space-y-3">
        <input type="hidden" id="prodId" value="0"/>
        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">Divisi</label>
          <select id="prodDiv" required class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs">
            <option value="paving">Paving Block</option>
            <option value="genteng">Genteng Pres</option>
            <option value="gapura">Jasa Gapura</option>
            <option value="renovasi">Renovasi Rumah</option>
          </select>
        </div>
        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">Nama Produk / Jasa</label>
          <input id="prodName" type="text" required placeholder="Contoh: Paving Bata 6cm K-300" class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs"/>
        </div>
        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">Spesifikasi</label>
          <input id="prodSpec" type="text" placeholder="Tebal, ukuran, kuat tekan..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs"/>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">Satuan</label>
            <input id="prodUnit" type="text" placeholder="m² / pcs / paket" required class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs"/>
          </div>
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">Harga (Rp)</label>
            <input id="prodPrice" type="number" required placeholder="65000" class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs"/>
          </div>
        </div>
        <div class="pt-3 flex justify-end gap-2">
          <button type="button" onclick="closeProductModal()" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200">Batal</button>
          <button type="submit" class="px-4 py-2 rounded-xl text-xs font-bold text-white bg-fk-blue hover:bg-blue-700">Simpan</button>
        </div>
      </form>
    </div>
  </div>

  <!-- MODAL SUPPLIER -->
  <div id="supplierModal" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 hidden">
    <div class="bg-white max-w-md w-full p-6 rounded-3xl border border-fk-border shadow-xl space-y-4">
      <h3 class="text-base font-bold text-fk-heading font-display" id="supplierModalTitle">Tambah Rekanan Supplier</h3>
      <form onsubmit="handleSaveSupplier(event)" class="space-y-3">
        <input type="hidden" id="suppId" value="0"/>
        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">Divisi</label>
          <select id="suppDiv" required class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs">
            <option value="paving">Paving Block</option>
            <option value="genteng">Genteng Pres</option>
            <option value="gapura">Jasa Gapura</option>
            <option value="renovasi">Renovasi Rumah</option>
          </select>
        </div>
        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">Nama Pabrik / Supplier</label>
          <input id="suppName" type="text" required placeholder="Nama vendor..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs"/>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">Nama PIC</label>
            <input id="suppPic" type="text" placeholder="Pak Slamet..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs"/>
          </div>
          <div>
            <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">No WhatsApp</label>
            <input id="suppPhone" type="text" placeholder="08..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs"/>
          </div>
        </div>
        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">Alamat Gudang / Pabrik</label>
          <input id="suppAddr" type="text" placeholder="Kota, kecamatan..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs"/>
        </div>
        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">Catatan HPP / Harga Modal</label>
          <input id="suppHpp" type="text" placeholder="Harga modal beli loco pabrik..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs"/>
        </div>
        <div>
          <label class="block text-[11px] font-bold uppercase tracking-wider text-fk-heading mb-1">Catatan Khusus</label>
          <textarea id="suppNotes" rows="2" placeholder="Minimal order, armada..." class="w-full bg-slate-50 border border-fk-border rounded-xl px-3 py-2 text-xs"></textarea>
        </div>
        <div class="pt-3 flex justify-end gap-2">
          <button type="button" onclick="closeSupplierModal()" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200">Batal</button>
          <button type="submit" class="px-4 py-2 rounded-xl text-xs font-bold text-white bg-fk-blue hover:bg-blue-700">Simpan</button>
        </div>
      </form>
    </div>
  </div>

  <script>
    let currentTab = 'leads';

    async function checkAuth() {
      try {
        const res = await fetch('/api/?action=auth_check');
        const data = await res.json();
        if (data.logged_in) {
          showDashboard();
        } else {
          showLogin();
        }
      } catch (e) {
        showLogin();
      }
    }

    function showLogin() {
      document.getElementById('loginSection').classList.remove('hidden');
      document.getElementById('dashSection').classList.add('hidden');
    }

    function showDashboard() {
      document.getElementById('loginSection').classList.add('hidden');
      document.getElementById('dashSection').classList.remove('hidden');
      loadStats();
      loadLeads();
    }

    async function handleLogin(e) {
      e.preventDefault();
      const pw = document.getElementById('loginPassword').value;
      const btn = document.getElementById('loginBtn');
      const err = document.getElementById('loginError');
      btn.disabled = true;
      btn.textContent = 'Memverifikasi...';
      err.classList.add('hidden');

      try {
        const res = await fetch('/api/?action=login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password: pw })
        });
        const data = await res.json();
        if (data.success) {
          showDashboard();
        } else {
          err.textContent = data.error || 'Password salah';
          err.classList.remove('hidden');
        }
      } catch (e) {
        err.textContent = 'Gagal menghubungi server';
        err.classList.remove('hidden');
      } finally {
        btn.disabled = false;
        btn.textContent = 'Masuk ke Dashboard';
      }
    }

    async function handleLogout() {
      await fetch('/api/?action=logout');
      showLogin();
    }

    function setTab(tab) {
      currentTab = tab;
      ['leads', 'products', 'suppliers', 'settings'].forEach(t => {
        const tabEl = document.getElementById('tab-' + t);
        const btnEl = document.getElementById('tabBtn-' + t);
        if (t === tab) {
          tabEl.classList.remove('hidden');
          btnEl.className = 'px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-fk-heading text-white transition-colors';
        } else {
          tabEl.classList.add('hidden');
          btnEl.className = 'px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold text-fk-body hover:bg-slate-200 transition-colors';
        }
      });

      if (tab === 'leads') loadLeads();
      else if (tab === 'products') loadProducts();
      else if (tab === 'suppliers') loadSuppliers();
      else if (tab === 'settings') loadSettings();
    }

    async function loadStats() {
      const res = await fetch('/api/?action=stats');
      const data = await res.json();
      if (data.success) {
        const s = data.stats;
        document.getElementById('statTotalLeads').textContent = s.total_leads;
        document.getElementById('statNewLeads').textContent = s.new_leads;
        document.getElementById('statDealLeads').textContent = s.deal_leads;
        document.getElementById('statValuation').textContent = 'Rp ' + Number(s.total_valuation || 0).toLocaleString('id-ID');
      }
    }

    async function loadLeads() {
      const div = document.getElementById('filterDivision').value;
      const status = document.getElementById('filterStatus').value;
      const res = await fetch(`/api/?action=get_leads&division=${div}&status=${status}`);
      const data = await res.json();
      const tbody = document.getElementById('leadsTableBody');

      if (!data.success || data.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="p-8 text-center text-slate-400">Belum ada data prospek yang sesuai filter.</td></tr>';
        document.getElementById('leadsCountLabel').textContent = '0 prospek ditemukan';
        return;
      }

      document.getElementById('leadsCountLabel').textContent = `${data.data.length} prospek ditemukan`;

      tbody.innerHTML = data.data.map(item => {
        const dateStr = item.created_at ? new Date(item.created_at).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '-';
        const cleanWa = item.whatsapp_number.replace(/[^0-9]/g, '');
        const waLink = cleanWa.startsWith('0') ? '62' + cleanWa.substring(1) : cleanWa;

        return `
          <tr class="hover:bg-slate-50/70 transition-colors">
            <td class="p-3.5 text-slate-500 whitespace-nowrap">${dateStr}</td>
            <td class="p-3.5">
              <div class="font-bold text-fk-heading">${escapeHtml(item.customer_name)}</div>
              <a href="https://wa.me/${waLink}" target="_blank" class="inline-flex items-center gap-1 text-fk-green hover:underline font-semibold mt-0.5">
                <span class="material-symbols-outlined text-[14px]">chat</span>
                <span>${escapeHtml(item.whatsapp_number)}</span>
              </a>
            </td>
            <td class="p-3.5">
              <span class="px-2 py-0.5 rounded-md font-bold uppercase text-[10px] ${getDivBadgeClass(item.division)}">
                ${item.division}
              </span>
            </td>
            <td class="p-3.5 font-medium text-slate-700">${escapeHtml(item.area_size || '-')}</td>
            <td class="p-3.5 text-slate-600">${escapeHtml(item.location || '-')}</td>
            <td class="p-3.5">
              <select onchange="updateLeadStatus(${item.id}, this.value)" class="bg-white border border-fk-border rounded-lg px-2 py-1 text-xs font-bold ${getStatusColorClass(item.status)}">
                <option value="BARU" ${item.status === 'BARU' ? 'selected' : ''}>BARU</option>
                <option value="SURVEY" ${item.status === 'SURVEY' ? 'selected' : ''}>SURVEY</option>
                <option value="PENAWARAN" ${item.status === 'PENAWARAN' ? 'selected' : ''}>PENAWARAN</option>
                <option value="DEAL" ${item.status === 'DEAL' ? 'selected' : ''}>DEAL</option>
                <option value="SELESAI" ${item.status === 'SELESAI' ? 'selected' : ''}>SELESAI</option>
                <option value="BATAL" ${item.status === 'BATAL' ? 'selected' : ''}>BATAL</option>
              </select>
            </td>
            <td class="p-3.5">
              <button onclick="deleteLead(${item.id})" class="text-rose-500 hover:text-rose-700 p-1" title="Hapus Lead">
                <span class="material-symbols-outlined text-[16px]">delete</span>
              </button>
            </td>
          </tr>
        `;
      }).join('');
    }

    function getDivBadgeClass(div) {
      if (div === 'paving') return 'bg-blue-100 text-blue-800';
      if (div === 'genteng') return 'bg-amber-100 text-amber-800';
      if (div === 'gapura') return 'bg-emerald-100 text-emerald-800';
      return 'bg-purple-100 text-purple-800';
    }

    function getStatusColorClass(st) {
      if (st === 'BARU') return 'text-blue-600';
      if (st === 'SURVEY') return 'text-amber-600';
      if (st === 'PENAWARAN') return 'text-purple-600';
      if (st === 'DEAL') return 'text-emerald-600';
      if (st === 'SELESAI') return 'text-slate-600';
      return 'text-rose-600';
    }

    async function updateLeadStatus(id, newStatus) {
      await fetch('/api/?action=update_lead_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, status: newStatus })
      });
      loadStats();
    }

    async function deleteLead(id) {
      if (!confirm('Hapus prospek ini?')) return;
      await fetch('/api/?action=delete_lead', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      loadLeads();
      loadStats();
    }

    // Product Functions
    async function loadProducts() {
      const res = await fetch('/api/?action=get_products');
      const data = await res.json();
      const tbody = document.getElementById('productsTableBody');
      if (!data.success || data.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center text-slate-400">Belum ada produk.</td></tr>';
        return;
      }
      tbody.innerHTML = data.data.map(p => `
        <tr class="hover:bg-slate-50/70">
          <td class="p-3.5"><span class="px-2 py-0.5 rounded font-bold uppercase text-[10px] ${getDivBadgeClass(p.division)}">${p.division}</span></td>
          <td class="p-3.5 font-bold text-fk-heading">${escapeHtml(p.name)}</td>
          <td class="p-3.5 text-slate-600">${escapeHtml(p.spec || '-')}</td>
          <td class="p-3.5 text-slate-700">${escapeHtml(p.unit)}</td>
          <td class="p-3.5 font-bold text-fk-blue">Rp ${Number(p.price).toLocaleString('id-ID')}</td>
          <td class="p-3.5">
            <button onclick='editProduct(${JSON.stringify(p)})' class="text-blue-600 hover:underline mr-2">Edit</button>
            <button onclick="deleteProduct(${p.id})" class="text-rose-500 hover:underline">Hapus</button>
          </td>
        </tr>
      `).join('');
    }

    function openProductModal() {
      document.getElementById('prodId').value = 0;
      document.getElementById('prodName').value = '';
      document.getElementById('prodSpec').value = '';
      document.getElementById('prodUnit').value = 'm²';
      document.getElementById('prodPrice').value = '';
      document.getElementById('productModalTitle').textContent = 'Tambah Produk Baru';
      document.getElementById('productModal').classList.remove('hidden');
    }

    function editProduct(p) {
      document.getElementById('prodId').value = p.id;
      document.getElementById('prodDiv').value = p.division;
      document.getElementById('prodName').value = p.name;
      document.getElementById('prodSpec').value = p.spec || '';
      document.getElementById('prodUnit').value = p.unit;
      document.getElementById('prodPrice').value = p.price;
      document.getElementById('productModalTitle').textContent = 'Edit Produk';
      document.getElementById('productModal').classList.remove('hidden');
    }

    function closeProductModal() {
      document.getElementById('productModal').classList.add('hidden');
    }

    async function handleSaveProduct(e) {
      e.preventDefault();
      const payload = {
        id: document.getElementById('prodId').value,
        division: document.getElementById('prodDiv').value,
        name: document.getElementById('prodName').value,
        spec: document.getElementById('prodSpec').value,
        unit: document.getElementById('prodUnit').value,
        price: document.getElementById('prodPrice').value
      };
      await fetch('/api/?action=save_product', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      closeProductModal();
      loadProducts();
    }

    async function deleteProduct(id) {
      if (!confirm('Hapus produk ini?')) return;
      await fetch('/api/?action=delete_product', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      loadProducts();
    }

    // Suppliers Functions
    async function loadSuppliers() {
      const res = await fetch('/api/?action=get_suppliers');
      const data = await res.json();
      const tbody = document.getElementById('suppliersTableBody');
      if (!data.success || data.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="p-8 text-center text-slate-400">Belum ada rekanan supplier.</td></tr>';
        return;
      }
      tbody.innerHTML = data.data.map(s => `
        <tr class="hover:bg-slate-50/70">
          <td class="p-3.5"><span class="px-2 py-0.5 rounded font-bold uppercase text-[10px] ${getDivBadgeClass(s.division)}">${s.division}</span></td>
          <td class="p-3.5 font-bold text-fk-heading">${escapeHtml(s.supplier_name)}</td>
          <td class="p-3.5">
            <div>${escapeHtml(s.pic_name || '-')}</div>
            <div class="text-slate-500 font-mono text-[11px]">${escapeHtml(s.phone || '-')}</div>
          </td>
          <td class="p-3.5 text-slate-600">${escapeHtml(s.address || '-')}</td>
          <td class="p-3.5 text-emerald-700 font-medium">${escapeHtml(s.hpp_notes || '-')}</td>
          <td class="p-3.5">
            <button onclick='editSupplier(${JSON.stringify(s)})' class="text-blue-600 hover:underline mr-2">Edit</button>
            <button onclick="deleteSupplier(${s.id})" class="text-rose-500 hover:underline">Hapus</button>
          </td>
        </tr>
      `).join('');
    }

    function openSupplierModal() {
      document.getElementById('suppId').value = 0;
      document.getElementById('suppName').value = '';
      document.getElementById('suppPic').value = '';
      document.getElementById('suppPhone').value = '';
      document.getElementById('suppAddr').value = '';
      document.getElementById('suppHpp').value = '';
      document.getElementById('suppNotes').value = '';
      document.getElementById('supplierModalTitle').textContent = 'Tambah Rekanan Supplier';
      document.getElementById('supplierModal').classList.remove('hidden');
    }

    function editSupplier(s) {
      document.getElementById('suppId').value = s.id;
      document.getElementById('suppDiv').value = s.division;
      document.getElementById('suppName').value = s.supplier_name;
      document.getElementById('suppPic').value = s.pic_name || '';
      document.getElementById('suppPhone').value = s.phone || '';
      document.getElementById('suppAddr').value = s.address || '';
      document.getElementById('suppHpp').value = s.hpp_notes || '';
      document.getElementById('suppNotes').value = s.notes || '';
      document.getElementById('supplierModalTitle').textContent = 'Edit Rekanan Supplier';
      document.getElementById('supplierModal').classList.remove('hidden');
    }

    function closeSupplierModal() {
      document.getElementById('supplierModal').classList.add('hidden');
    }

    async function handleSaveSupplier(e) {
      e.preventDefault();
      const payload = {
        id: document.getElementById('suppId').value,
        division: document.getElementById('suppDiv').value,
        supplier_name: document.getElementById('suppName').value,
        pic_name: document.getElementById('suppPic').value,
        phone: document.getElementById('suppPhone').value,
        address: document.getElementById('suppAddr').value,
        hpp_notes: document.getElementById('suppHpp').value,
        notes: document.getElementById('suppNotes').value
      };
      await fetch('/api/?action=save_supplier', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      closeSupplierModal();
      loadSuppliers();
    }

    async function deleteSupplier(id) {
      if (!confirm('Hapus supplier ini?')) return;
      await fetch('/api/?action=delete_supplier', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      loadSuppliers();
    }

    // Settings Functions
    async function loadSettings() {
      const res = await fetch('/api/?action=get_settings');
      const data = await res.json();
      if (data.success) {
        document.getElementById('set_wa_paving').value = data.data.wa_paving || '';
        document.getElementById('set_wa_genteng').value = data.data.wa_genteng || '';
        document.getElementById('set_wa_gapura').value = data.data.wa_gapura || '';
        document.getElementById('set_wa_renovasi').value = data.data.wa_renovasi || '';
      }
    }

    async function handleSaveSettings(e) {
      e.preventDefault();
      const msg = document.getElementById('settingsMsg');
      const payload = {
        wa_paving: document.getElementById('set_wa_paving').value,
        wa_genteng: document.getElementById('set_wa_genteng').value,
        wa_gapura: document.getElementById('set_wa_gapura').value,
        wa_renovasi: document.getElementById('set_wa_renovasi').value,
        new_password: document.getElementById('set_new_password').value
      };
      await fetch('/api/?action=save_settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      msg.textContent = 'Pengaturan berhasil disimpan!';
      msg.classList.remove('hidden');
      document.getElementById('set_new_password').value = '';
      setTimeout(() => msg.classList.add('hidden'), 3000);
    }

    function escapeHtml(text) {
      if (!text) return '';
      return String(text).replace(/[&<>"']/g, function(m) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
      });
    }

    // Start
    checkAuth();
  </script>
</body>
</html>

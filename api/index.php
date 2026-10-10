<?php
// API Controller for FirKaizen Material & Konstruksi
header('Content-Type: application/json; charset=utf-8');
session_start();

$dbPath = __DIR__ . '/../data/database.sqlite';
$db = new SQLite3($dbPath);
$db->busyTimeout(5000);

// Initialize schema if not exists
$db->exec("
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    division TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    whatsapp_number TEXT NOT NULL,
    area_size TEXT,
    location TEXT,
    estimated_cost INTEGER DEFAULT 0,
    status TEXT DEFAULT 'BARU',
    notes TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    division TEXT NOT NULL,
    name TEXT NOT NULL,
    spec TEXT,
    unit TEXT DEFAULT 'm²',
    price INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    division TEXT NOT NULL,
    supplier_name TEXT NOT NULL,
    pic_name TEXT,
    phone TEXT,
    address TEXT,
    hpp_notes TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
");

// Seed initial settings & products if empty
$initCheck = $db->querySingle("SELECT COUNT(*) FROM settings");
if ($initCheck == 0) {
    // Default admin password diambil dari env FK_ADMIN_DEFAULT_PASSWORD (jangan hardcode credential di repo)
    $defaultPassHash = password_hash(getenv('FK_ADMIN_DEFAULT_PASSWORD') ?: bin2hex(random_bytes(12)), PASSWORD_BCRYPT);
    $stmt = $db->prepare("INSERT INTO settings (key, value) VALUES ('admin_password_hash', :h), ('wa_paving', '6285196135691'), ('wa_genteng', '6285196135691'), ('wa_gapura', '6285196135691'), ('wa_renovasi', '6285196135691')");
    $stmt->bindValue(':h', $defaultPassHash, SQLITE3_TEXT);
    $stmt->execute();

    // Initial products
    $productsSeed = [
        ['paving', 'Paving Bata (Holland) 6cm K-300', 'Tebal 6 cm, isi 44 pcs/m², kuat tekan K-300', 'm²', 65000],
        ['paving', 'Paving Bata (Holland) 8cm K-400', 'Tebal 8 cm, isi 44 pcs/m², kuat tekan K-400 truk', 'm²', 78000],
        ['paving', 'Paving Segi Enam (Hexagon) 6cm', 'Tebal 6 cm, isi 27 pcs/m², estetik modern', 'm²', 72000],
        ['paving', 'Kanstin Beton Taman (Jepit)', 'Ukuran 40 x 20 x 10 cm, pembatas paving', 'pcs', 18000],
        ['paving', 'Jasa Pasang Paving + Stamper', 'Tenaga tukang spesialis + abu batu + pemadatan stamper', 'm²', 25000],
        ['genteng', 'Genteng Pres Mantili Super', 'Tanah liat presisi bakar oven, isi 24 pcs/m²', 'pcs', 2600],
        ['genteng', 'Genteng Morando Glazur', 'Lapisan glazur kilap anti lumut, isi 18 pcs/m²', 'pcs', 4500],
        ['genteng', 'Genteng Flat Beton Minimalis', 'Beton padat finishing cat oven modern, isi 10 pcs/m²', 'pcs', 8500],
        ['genteng', 'Jasa Pasang Rangka Atap Baja Ringan', 'Baja ringan 0.75mm SNI + reng + baut bergaransi', 'm²', 125000],
        ['gapura', 'Gapura Perumahan Cluster Minimalis', 'Struktur beton bertulang + ornamen roster & batu alam', 'paket', 15000000],
        ['gapura', 'Gapura Batas Desa / Kampung', 'Lebar bentang 4-6 meter, cat duco + plat nama desa', 'paket', 22000000],
        ['renovasi', 'Jasa Renovasi Atap Bocor & Dak', 'Waterproofing membran + ganti usuk/reng rusak', 'titik', 350000],
        ['renovasi', 'Borongan Bangun / Renovasi Rumah', 'Tenaga + material standar SNI dengan kontrak & termin', 'm²', 2800000]
    ];

    $pStmt = $db->prepare("INSERT INTO products (division, name, spec, unit, price) VALUES (:div, :name, :spec, :unit, :price)");
    foreach ($productsSeed as $p) {
        $pStmt->bindValue(':div', $p[0], SQLITE3_TEXT);
        $pStmt->bindValue(':name', $p[1], SQLITE3_TEXT);
        $pStmt->bindValue(':spec', $p[2], SQLITE3_TEXT);
        $pStmt->bindValue(':unit', $p[3], SQLITE3_TEXT);
        $pStmt->bindValue(':price', $p[4], SQLITE3_INTEGER);
        $pStmt->execute();
    }

    // Initial suppliers seed
    $suppSeed = [
        ['paving', 'Pabrik Precast Solo Raya', 'Pak Slamet', '081234567891', 'Mojolaban, Sukoharjo', 'Modal paving bata K-300 Rp 52.000/m²', 'Armada dump truck 4 unit, ready 1.000 m²/hari'],
        ['genteng', 'Sentra Genteng Kebumen & Jatiwangi', 'Haji Mulyono', '081234567892', 'Kebumen / Pengiriman via Truk Colt', 'Modal Mantili Rp 2.050/pcs loco pabrik', 'Minimal kirim 1 colt (3.000 pcs)'],
        ['gapura', 'Mandor Arsitektur Mas Bowo', 'Mas Bowo', '081234567893', 'Karanganyar', 'Tenaga borongan 3 tukang + 2 laden', 'Spesialis bata ekspos & ukir semen minimalis'],
        ['renovasi', 'CV Mandor Berkah Bangun', 'Pak Darno', '081234567894', 'Surakarta', 'Sistem harian Rp 130rb/tukang, Rp 90rb/laden', 'Berpengalaman renovasi ruko & rumah tinggal 15 tahun']
    ];

    $sStmt = $db->prepare("INSERT INTO suppliers (division, supplier_name, pic_name, phone, address, hpp_notes, notes) VALUES (:div, :sname, :pic, :phone, :addr, :hpp, :notes)");
    foreach ($suppSeed as $s) {
        $sStmt->bindValue(':div', $s[0], SQLITE3_TEXT);
        $sStmt->bindValue(':sname', $s[1], SQLITE3_TEXT);
        $sStmt->bindValue(':pic', $s[2], SQLITE3_TEXT);
        $sStmt->bindValue(':phone', $s[3], SQLITE3_TEXT);
        $sStmt->bindValue(':addr', $s[4], SQLITE3_TEXT);
        $sStmt->bindValue(':hpp', $s[5], SQLITE3_TEXT);
        $sStmt->bindValue(':notes', $s[6], SQLITE3_TEXT);
        $sStmt->execute();
    }
}

// Router
$action = $_GET['action'] ?? '';
$method = $_SERVER['REQUEST_METHOD'];
$body = json_decode(file_get_contents('php://input'), true) ?? [];

// Public Endpoints
if ($action === 'submit_lead') {
    $div = trim($body['division'] ?? 'paving');
    $name = trim($body['customer_name'] ?? '');
    $phone = trim($body['whatsapp_number'] ?? '');
    $area = trim($body['area_size'] ?? '');
    $location = trim($body['location'] ?? '');
    $cost = intval($body['estimated_cost'] ?? 0);
    $notes = trim($body['notes'] ?? '');

    if (!$name || !$phone) {
        echo json_encode(['success' => false, 'error' => 'Nama dan nomor WhatsApp wajib diisi']);
        exit;
    }

    $stmt = $db->prepare("INSERT INTO leads (division, customer_name, whatsapp_number, area_size, location, estimated_cost, status, notes) VALUES (:div, :name, :phone, :area, :loc, :cost, 'BARU', :notes)");
    $stmt->bindValue(':div', $div, SQLITE3_TEXT);
    $stmt->bindValue(':name', $name, SQLITE3_TEXT);
    $stmt->bindValue(':phone', $phone, SQLITE3_TEXT);
    $stmt->bindValue(':area', $area, SQLITE3_TEXT);
    $stmt->bindValue(':loc', $location, SQLITE3_TEXT);
    $stmt->bindValue(':cost', $cost, SQLITE3_INTEGER);
    $stmt->bindValue(':notes', $notes, SQLITE3_TEXT);
    $stmt->execute();

    $leadId = $db->lastInsertRowID();

    // Get specific WA dispatch number
    $waNumber = $db->querySingle("SELECT value FROM settings WHERE key = 'wa_" . SQLite3::escapeString($div) . "'") ?: '6285196135691';

    echo json_encode([
        'success' => true,
        'lead_id' => $leadId,
        'dispatch_wa' => $waNumber
    ]);
    exit;
}

if ($action === 'get_public_products') {
    $div = $_GET['division'] ?? '';
    $sql = "SELECT id, division, name, spec, unit, price FROM products WHERE is_active = 1";
    if ($div) {
        $sql .= " AND division = '" . SQLite3::escapeString($div) . "'";
    }
    $res = $db->query($sql);
    $items = [];
    while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
        $items[] = $row;
    }
    echo json_encode(['success' => true, 'data' => $items]);
    exit;
}

if ($action === 'login') {
    $password = $body['password'] ?? '';
    $hash = $db->querySingle("SELECT value FROM settings WHERE key = 'admin_password_hash'");
    if (password_verify($password, $hash)) {
        $_SESSION['fk_admin_logged'] = true;
        echo json_encode(['success' => true]);
    } else {
        echo json_encode(['success' => false, 'error' => 'Password admin salah']);
    }
    exit;
}

if ($action === 'logout') {
    unset($_SESSION['fk_admin_logged']);
    session_destroy();
    echo json_encode(['success' => true]);
    exit;
}

if ($action === 'auth_check') {
    echo json_encode(['logged_in' => !empty($_SESSION['fk_admin_logged'])]);
    exit;
}

// Protected Admin Endpoints
if (empty($_SESSION['fk_admin_logged'])) {
    http_response_code(401);
    echo json_encode(['success' => false, 'error' => 'Unauthorized']);
    exit;
}

// 1. Dashboard Stats
if ($action === 'stats') {
    $totalLeads = $db->querySingle("SELECT COUNT(*) FROM leads");
    $newLeads = $db->querySingle("SELECT COUNT(*) FROM leads WHERE status = 'BARU'");
    $dealLeads = $db->querySingle("SELECT COUNT(*) FROM leads WHERE status IN ('DEAL', 'SELESAI')");
    $totalValuation = $db->querySingle("SELECT SUM(estimated_cost) FROM leads WHERE status IN ('DEAL', 'PENAWARAN', 'SURVEY')") ?: 0;

    $divBreakdown = [];
    $divRes = $db->query("SELECT division, COUNT(*) as count, SUM(estimated_cost) as total_val FROM leads GROUP BY division");
    while ($r = $divRes->fetchArray(SQLITE3_ASSOC)) {
        $divBreakdown[$r['division']] = [
            'count' => intval($r['count']),
            'valuation' => intval($r['total_val'] ?: 0)
        ];
    }

    echo json_encode([
        'success' => true,
        'stats' => [
            'total_leads' => $totalLeads,
            'new_leads' => $newLeads,
            'deal_leads' => $dealLeads,
            'total_valuation' => $totalValuation,
            'by_division' => $divBreakdown
        ]
    ]);
    exit;
}

// 2. Leads CRUD
if ($action === 'get_leads') {
    $div = $_GET['division'] ?? '';
    $status = $_GET['status'] ?? '';
    $sql = "SELECT * FROM leads WHERE 1=1";
    if ($div) $sql .= " AND division = '" . SQLite3::escapeString($div) . "'";
    if ($status) $sql .= " AND status = '" . SQLite3::escapeString($status) . "'";
    $sql .= " ORDER BY id DESC LIMIT 100";

    $res = $db->query($sql);
    $leads = [];
    while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
        $leads[] = $row;
    }
    echo json_encode(['success' => true, 'data' => $leads]);
    exit;
}

if ($action === 'update_lead_status') {
    $id = intval($body['id'] ?? 0);
    $status = trim($body['status'] ?? 'BARU');
    $notes = trim($body['notes'] ?? '');

    $stmt = $db->prepare("UPDATE leads SET status = :st, notes = CASE WHEN :nt != '' THEN :nt ELSE notes END WHERE id = :id");
    $stmt->bindValue(':st', $status, SQLITE3_TEXT);
    $stmt->bindValue(':nt', $notes, SQLITE3_TEXT);
    $stmt->bindValue(':id', $id, SQLITE3_INTEGER);
    $stmt->execute();

    echo json_encode(['success' => true]);
    exit;
}

if ($action === 'delete_lead') {
    $id = intval($body['id'] ?? 0);
    $db->exec("DELETE FROM leads WHERE id = " . $id);
    echo json_encode(['success' => true]);
    exit;
}

// 3. Products CRUD
if ($action === 'get_products') {
    $res = $db->query("SELECT * FROM products ORDER BY division, id ASC");
    $items = [];
    while ($r = $res->fetchArray(SQLITE3_ASSOC)) $items[] = $r;
    echo json_encode(['success' => true, 'data' => $items]);
    exit;
}

if ($action === 'save_product') {
    $id = intval($body['id'] ?? 0);
    $div = trim($body['division'] ?? 'paving');
    $name = trim($body['name'] ?? '');
    $spec = trim($body['spec'] ?? '');
    $unit = trim($body['unit'] ?? 'm²');
    $price = intval($body['price'] ?? 0);

    if ($id > 0) {
        $stmt = $db->prepare("UPDATE products SET division = :d, name = :n, spec = :s, unit = :u, price = :p WHERE id = :id");
        $stmt->bindValue(':id', $id, SQLITE3_INTEGER);
    } else {
        $stmt = $db->prepare("INSERT INTO products (division, name, spec, unit, price) VALUES (:d, :n, :s, :u, :p)");
    }
    $stmt->bindValue(':d', $div, SQLITE3_TEXT);
    $stmt->bindValue(':n', $name, SQLITE3_TEXT);
    $stmt->bindValue(':s', $spec, SQLITE3_TEXT);
    $stmt->bindValue(':u', $unit, SQLITE3_TEXT);
    $stmt->bindValue(':p', $price, SQLITE3_INTEGER);
    $stmt->execute();

    echo json_encode(['success' => true]);
    exit;
}

if ($action === 'delete_product') {
    $id = intval($body['id'] ?? 0);
    $db->exec("DELETE FROM products WHERE id = " . $id);
    echo json_encode(['success' => true]);
    exit;
}

// 4. Suppliers CRUD
if ($action === 'get_suppliers') {
    $res = $db->query("SELECT * FROM suppliers ORDER BY division, id ASC");
    $items = [];
    while ($r = $res->fetchArray(SQLITE3_ASSOC)) $items[] = $r;
    echo json_encode(['success' => true, 'data' => $items]);
    exit;
}

if ($action === 'save_supplier') {
    $id = intval($body['id'] ?? 0);
    $div = trim($body['division'] ?? 'paving');
    $sname = trim($body['supplier_name'] ?? '');
    $pic = trim($body['pic_name'] ?? '');
    $phone = trim($body['phone'] ?? '');
    $addr = trim($body['address'] ?? '');
    $hpp = trim($body['hpp_notes'] ?? '');
    $notes = trim($body['notes'] ?? '');

    if ($id > 0) {
        $stmt = $db->prepare("UPDATE suppliers SET division = :d, supplier_name = :sn, pic_name = :pic, phone = :ph, address = :ad, hpp_notes = :hpp, notes = :nt WHERE id = :id");
        $stmt->bindValue(':id', $id, SQLITE3_INTEGER);
    } else {
        $stmt = $db->prepare("INSERT INTO suppliers (division, supplier_name, pic_name, phone, address, hpp_notes, notes) VALUES (:d, :sn, :pic, :ph, :ad, :hpp, :nt)");
    }
    $stmt->bindValue(':d', $div, SQLITE3_TEXT);
    $stmt->bindValue(':sn', $sname, SQLITE3_TEXT);
    $stmt->bindValue(':pic', $pic, SQLITE3_TEXT);
    $stmt->bindValue(':ph', $phone, SQLITE3_TEXT);
    $stmt->bindValue(':ad', $addr, SQLITE3_TEXT);
    $stmt->bindValue(':hpp', $hpp, SQLITE3_TEXT);
    $stmt->bindValue(':nt', $notes, SQLITE3_TEXT);
    $stmt->execute();

    echo json_encode(['success' => true]);
    exit;
}

if ($action === 'delete_supplier') {
    $id = intval($body['id'] ?? 0);
    $db->exec("DELETE FROM suppliers WHERE id = " . $id);
    echo json_encode(['success' => true]);
    exit;
}

// 5. Settings CRUD
if ($action === 'get_settings') {
    $res = $db->query("SELECT key, value FROM settings WHERE key != 'admin_password_hash'");
    $items = [];
    while ($r = $res->fetchArray(SQLITE3_ASSOC)) $items[$r['key']] = $r['value'];
    echo json_encode(['success' => true, 'data' => $items]);
    exit;
}

if ($action === 'save_settings') {
    $stmt = $db->prepare("INSERT OR REPLACE INTO settings (key, value) VALUES (:k, :v)");
    foreach ($body as $k => $v) {
        if ($k === 'new_password' && !empty($v)) {
            $stmt->bindValue(':k', 'admin_password_hash', SQLITE3_TEXT);
            $stmt->bindValue(':v', password_hash($v, PASSWORD_BCRYPT), SQLITE3_TEXT);
            $stmt->execute();
        } elseif ($k !== 'new_password') {
            $stmt->bindValue(':k', $k, SQLITE3_TEXT);
            $stmt->bindValue(':v', strval($v), SQLITE3_TEXT);
            $stmt->execute();
        }
    }
    echo json_encode(['success' => true]);
    exit;
}

echo json_encode(['error' => 'Unknown endpoint']);

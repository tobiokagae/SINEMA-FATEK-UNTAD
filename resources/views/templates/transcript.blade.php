<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Transkrip Ekstrakurikuler - {{ $student->nim }}</title>
    <style>
        @page {
            margin-top: 10px;
            margin-bottom: 20px;
            margin-left: 40px;
            margin-right: 40px;
        }

        body {
            font-family: 'Times New Roman', Times, serif;
            font-size: 12pt;
            margin: 30px;
        }

        /* --- STYLE UNTUK KOP SURAT --- */
        .letterhead-table {
            width: 100%;
            border-bottom: 2px solid black;
            padding-bottom: 5px;
        }

        .logo {
            width: 100px;
        }

        .kop-text {
            text-align: center;
            line-height: 1.2;
        }

        .kop-text .line1 {
            font-size: 12pt;
        }

        .kop-text .line2 {
            font-size: 14pt;
            font-weight: bold;
        }

        .kop-text .line3 {
            font-size: 16pt;
            font-weight: bold;
        }

        .kop-text .address {
            font-size: 9pt;
            font-weight: normal;
        }

        .header {
            text-align: center;
            font-weight: bold;
            font-size: 14pt;
            margin-top: 30px;
            margin-bottom: 30px;
        }

        .student-info {
            width: 100%;
            margin-bottom: 20px;
            border-spacing: 0;
        }

        .student-info td {
            padding: 2px 0;
        }

        .info-label {
            width: 200px;
        }

        .info-separator {
            width: 10px;
        }

        .scores-table {
            width: 100%;
            border: 1px solid black;
            border-collapse: collapse;
        }

        .scores-table th,
        .scores-table td {
            border: 1px solid black;
            padding: 8px;
            text-align: left;
        }

        .scores-table th {
            font-weight: bold;
            background-color: #f2f2f2;
        }

        .scores-table .center {
            text-align: center;
        }

        .scores-table .total-label {
            font-weight: bold;
            text-align: right;
        }

        /* --- SIGNATURE BLOCK --- */
        .signature-block {
            margin-top: 20px;
            text-align: center;
            page-break-inside: avoid !important;
        }

        .signature-space {
            position: relative;
            height: 60px;
            /* ruang untuk cap + ttd */
        }

        .stamp-image {
            position: absolute;
            left: 35%;
            /* agak kiri */
            top: -50px;
            width: 160px;
            opacity: 1.0;
            transform: translateX(-50%) rotate(-5deg);
            /* miring sedikit */
            z-index: 1;
        }

        .signature-image {
            position: absolute;
            left: 50%;
            /* agak ke kanan dari cap */
            top: -10px;
            height: 80px;
            transform: translateX(-50%);
            z-index: 2;
        }

        .signature-name {
            top: -20px;
            font-weight: bold;
            text-decoration: underline;
        }

        /* --- STYLE UNTUK LAMPIRAN --- */
        .page-break {
            page-break-before: always;
            margin-bottom: 20px;
        }

        .appendix-table {
            font-size: 11pt !important;
        }
    </style>
</head>

<body>

    {{-- KOP SURAT --}}
    <table class="letterhead-table">
        <tr>
            <td style="width: 15%;">
                @if($logoPath)
                <img src="{{ storage_path('app/public/' . $logoPath) }}" alt="Logo Untad" class="logo">
                @else
                <div style="width: 80px; height: 80px; border: 1px solid #ccc; 
                                text-align: center; line-height: 80px; font-size: 10px;">
                    Logo
                </div>
                @endif
            </td>
            <td style="width: 85%;" class="kop-text">
                <div class="line1">KEMENTERIAN PENDIDIKAN TINGGI, SAINS, DAN TEKNOLOGI</div>
                <div class="line2">UNIVERSITAS TADULAKO</div>
                <div class="line3">FAKULTAS {{ strtoupper($student->faculty->name) }}</div>
                <div class="address">
                    Jalan Soekarno Hatta Kilometer 9 Tondo, Mantikulore, Palu<br>
                    Surel: {{ $student->faculty->email ?? '(Email Belum Diatur)' }}
                    Laman: {{ $student->faculty->website ?? '(Website Belum Diatur)' }}
                    Telepon: {{ $student->faculty->phone ?? '(Telepon Belum Diatur)' }}
                </div>
            </td>
        </tr>
    </table>

    <div class="header">
        TRANSKRIP EKSTRAKURIKULER MAHASISWA<br>
        <span style="font-weight: normal; font-size: 12pt;">
            Nomor: {{ $documentNumber ?? '(Belum Diatur)' }}
        </span>
    </div>

    <table class="student-info">
        <tr>
            <td class="info-label">NAMA MAHASISWA</td>
            <td class="info-separator">:</td>
            <td>{{ strtoupper($student->user->name) }}</td>
        </tr>
        <tr>
            <td class="info-label">STAMBUK</td>
            <td class="info-separator">:</td>
            <td>{{ $student->nim }}</td>
        </tr>
        <tr>
            <td class="info-label">PROGRAM STUDI</td>
            <td class="info-separator">:</td>
            <td>{{ strtoupper($student->studyProgram->name) }}</td>
        </tr>
    </table>

    <table class="scores-table">
        <thead>
            <tr>
                <th class="center" style="width: 5%;">No.</th>
                <th style="width: 75%;">Kriteria Kegiatan Ekstrakurikuler Mahasiswa</th>
                <th class="center" style="width: 20%;">Poin</th>
            </tr>
        </thead>
        <tbody>
            @foreach($allFields as $field)
            <tr>
                <td class="center">{{ $loop->iteration }}.</td>
                <td>{{ $field->name }}</td>
                <td class="center">{{ $scoresByField[$field->id] ?? 0 }}</td>
            </tr>
            @endforeach
            <tr>
                <td colspan="2" class="total-label">Total Perolehan Poin</td>
                <td class="center" style="font-weight: bold;">{{ $totalScore }}</td>
            </tr>
            <tr>
                <td colspan="2" class="total-label">Nilai Mutu</td>
                <td class="center" style="font-weight: bold;">{{ $nilaiMutu }}</td>
            </tr>
        </tbody>
    </table>

    <div class="signature-block">
        <p>Palu, {{ $documentDate ? \Carbon\Carbon::parse($documentDate)->translatedFormat('d F Y') :
            \Carbon\Carbon::now()->translatedFormat('d F Y') }}</p>
        <p>Menyetujui,<br>a.n. Dekan</p>
        <p>{{ $signatory->jabatan ?? 'Wakil Dekan Bidang Kemahasiswaan dan Alumni' }}</p>

        <div class="signature-space">
            @if($signatory?->stamp_image_path)
            <img src="{{ storage_path('app/public/' . $signatory->stamp_image_path) }}" alt="Cap Fakultas"
                class="stamp-image">
            @endif
            @if($signatory?->signature_image_path)
            <img src="{{ storage_path('app/public/' . $signatory->signature_image_path) }}" alt="Tanda Tangan"
                class="signature-image">
            @endif
        </div>

        <p>
            <span class="signature-name">{{ $signatory->name ?? '(Nama Belum Diatur)' }}</span><br />
            NIP. {{ $signatory->nip ?? '(NIP Belum Diatur)' }}
        </p>
    </div>

    @include('templates.transcript_appendix')

</body>

</html>

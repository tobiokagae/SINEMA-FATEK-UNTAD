{{-- File: resources/views/templates/transcript_appendix.blade.php --}}
<div class="page-break"></div>

<div class="header" style="text-decoration: underline; margin-top: 0;">
    LAMPIRAN: RINCIAN KEGIATAN EKSTRAKURIKULER
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

<table class="scores-table appendix-table">
    <thead>
        <tr>
            <th class="center" style="width: 5%;">No.</th>
            <th class="center" style="width: 15%;">Tanggal</th>
            <th>Nama Kegiatan</th>
            <th class="center" style="width: 10%;">Poin</th>
        </tr>
    </thead>
    <tbody>
        @if($verifiedSubmissions->isEmpty())
        <tr>
            <td colspan="4" class="center" style="padding: 20px;">Belum ada kegiatan yang diverifikasi.</td>
        </tr>
        @else
        @foreach($verifiedSubmissions as $submission)
        <tr>
            <td class="center">{{ $loop->iteration }}.</td>
            <td class="center">{{ \Carbon\Carbon::parse($submission->activity_start_date)->translatedFormat('d M Y') }}
            </td>
            <td>
                {{ $submission->activityType->name }}
                {{-- Tampilkan detail Tingkat dan Jabatan jika ada --}}
                @if($submission->activityType->level || $submission->activityType->achievement)
                <span style="font-size: 10pt; color: #555; display: block;">
                    (
                    {{ implode(' - ', array_filter([$submission->activityType->level,
                    $submission->activityType->achievement])) }}
                    )
                </span>
                @endif
            </td>
            <td class="center">{{ $submission->activityType->score }}</td>
        </tr>
        @endforeach
        @endif
    </tbody>
    <tfoot>
        <tr>
            <td colspan="3" class="total-label">Total Perolehan Poin</td>
            <td class="center" style="font-weight: bold;">{{ $totalScore }}</td>
        </tr>
        <tr>
            <td colspan="3" class="total-label">Nilai Mutu</td>
            <td class="center" style="font-weight: bold;">{{ $nilaiMutu }}</td>
        </tr>
    </tfoot>
</table>

<div style="font-size: 8pt; margin-top: 5px;">
    <strong>Keterangan:</strong>
    <span>
        Nilai Mutu berdasarkan total perolehan poin:
        <strong>A</strong> (>3000),
        <strong>A-</strong> (2501-3000),
        <strong>B+</strong> (2001-2500),
        <strong>B</strong> (1500-2000).
    </span>
</div>

{{-- Tanda tangan di halaman lampiran --}}
<div class="signature-block">
    <p>Palu, {{ $documentDate ? \Carbon\Carbon::parse($documentDate)->translatedFormat('d F Y') :
        \Carbon\Carbon::now()->translatedFormat('d F Y') }}</p>
    <p>Menyetujui,<br>a.n. Dekan</p>
    <p>{{ $signatory->jabatan ?? 'Wakil Dekan Bidang Kemahasiswaan dan Alumni' }}</p>

    <div class="signature-space">
        @if($signatory?->stamp_image_path)
        <img src="{{ storage_path('app/public/' . $signatory->stamp_image_path) }}" alt="Cap Fakultas" class="stamp-image">
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

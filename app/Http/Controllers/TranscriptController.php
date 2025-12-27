<?php

// File: app/Http/Controllers/TranscriptController.php

namespace App\Http\Controllers;

use App\Models\ActivityField;
use App\Models\Setting;
use App\Models\Student;
use App\Models\TranscriptRequest;
use Barryvdh\DomPDF\Facade\Pdf;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Storage;

class TranscriptController extends Controller
{
    public function preview(TranscriptRequest $transcriptRequest)
    {
# dd(public_path());
        // Pastikan hanya admin yang bisa akses preview
        abort_if(Auth::user()->role === 'Student', 403);

        $student = $transcriptRequest->student;
        return $this->buildPdf($student)->stream('preview.pdf');
    }

    public function generate(Student $student, ?TranscriptRequest $transcriptRequest = null)
    {
        $user = Auth::user();

        $isOwner = ($user->role === 'Student' && $user->id === $student->user_id);
        $isAdmin = ($user->role === 'Admin');

        if (!$isOwner && !$isAdmin) {
            abort(403, 'Akses Ditolak.');
        }

        // --- PERBAIKAN: Gunakan metode buildPdf() yang bisa dipakai ulang ---
        $pdf = $this->buildPdf($student, $transcriptRequest);

        // Jika ini adalah bagian dari proses persetujuan, simpan file
        if ($transcriptRequest && $transcriptRequest->document_number) {
            $filename = 'transcripts/TEM_' . $student->nim . '_' . time() . '.pdf';
            Storage::disk('public')->put($filename, $pdf->output());
            $transcriptRequest->update(['file_path' => $filename]);
        }

        return $pdf->stream('transkrip-' . $student->nim . '.pdf');
    }

    /**
     * Helper function untuk membangun objek PDF.
     */
    private function buildPdf(Student $student, ?TranscriptRequest $transcriptRequest = null)
    {
        $allFields = ActivityField::orderBy('id')->get();
        $signatory = $student->faculty->signatory;
        $logoPath = Setting::where('key', 'kop_surat_logo')->first()?->value;

        $verifiedSubmissions = $student->submissions()
            ->where('status', 'Verified')
            ->with('activityType.activityField')
            ->orderBy('certificate_date', 'asc')
            ->get();

        $scoresByField = $verifiedSubmissions
            ->groupBy('activityType.activity_field_id')
            ->map(fn($group) => $group->sum('activityType.score'));

        $totalScore = $scoresByField->sum();

        $nilaiMutu = match (true) {
            $totalScore > 3000 => 'A',
            $totalScore >= 2501 => 'A-',
            $totalScore >= 2001 => 'B+',
            $totalScore >= 1500 => 'B',
            default => '-',
        };

        return Pdf::loadView('templates.transcript', [
            'student' => $student,
            'allFields' => $allFields,
            'scoresByField' => $scoresByField,
            'totalScore' => $totalScore,
            'nilaiMutu' => $nilaiMutu,
            'signatory' => $signatory,
            'logoPath' => $logoPath,
            'verifiedSubmissions' => $verifiedSubmissions,
            // Kirim data nomor & tanggal surat ke template
            'documentNumber' => $transcriptRequest?->document_number,
            'documentDate' => $transcriptRequest?->document_date,
        ]);
    }
}

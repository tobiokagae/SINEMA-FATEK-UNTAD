<?php

namespace App\Rules;

use App\Models\Setting;
use Closure;
use Illuminate\Contracts\Validation\ValidationRule;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Collection;

class ValidClaimDate implements ValidationRule
{
    /**
     * Jalankan aturan validasi.
     *
     * @param  \Closure(string): \Illuminate\Translation\PotentiallyTranslatedString  $fail
     */
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        // Pengecualian: Jika pengguna adalah Admin, lewati semua validasi.
        if (Auth::user()?->role === 'Admin') {
            return;
        }

        // Ambil pengaturan yang aktif dari database
        $settings = Setting::whereIn('key', [
            'claim_restriction_mode',
            'claim_max_days',
            'semester_ganjil_start_month',
            'semester_ganjil_end_month',
            'semester_genap_start_month',
            'semester_genap_end_month',
        ])->pluck('value', 'key');

        $mode = $settings->get('claim_restriction_mode', 'none');
        $certificateDate = Carbon::parse($value);

        // Jalankan validasi berdasarkan mode yang dipilih
        match ($mode) {
            'days' => $this->validateByDays($certificateDate, $settings, $fail),
            'semester' => $this->validateBySemester($certificateDate, $settings, $fail),
            default => null, // 'none' atau mode tidak dikenal tidak melakukan apa-apa
        };
    }

    // Logika validasi untuk Opsi A: Berdasarkan Jumlah Hari
    private function validateByDays(Carbon $certificateDate, Collection $settings, Closure $fail): void
    {
        $maxDays = (int) $settings->get('claim_max_days', 90);
        $limitDate = now()->subDays($maxDays)->startOfDay();

        if ($certificateDate->isBefore($limitDate)) {
            $fail("Klaim tidak valid. Batas maksimal pengajuan adalah {$maxDays} hari setelah sertifikat terbit.");
        }
    }

    // Logika validasi untuk Opsi B: Berdasarkan Periode Semester (dengan pengecekan tahun)
    private function validateBySemester(Carbon $certificateDate, Collection $settings, Closure $fail): void
    {
        $ganjilStart = (int) $settings->get('semester_ganjil_start_month', 1);
        $ganjilEnd = (int) $settings->get('semester_ganjil_end_month', 6);
        $genapStart = (int) $settings->get('semester_genap_start_month', 7);
        $genapEnd = (int) $settings->get('semester_genap_end_month', 12);

        $now = now();
        $currentYear = $now->year;
        $currentMonth = $now->month;

        $certificateYear = $certificateDate->year;
        $certificateMonth = $certificateDate->month;

        // --- PERBAIKAN UTAMA: Cek tahun terlebih dahulu ---
        if ($currentYear !== $certificateYear) {
            $fail("Klaim tidak valid. Sertifikat dari tahun {$certificateYear} tidak bisa diklaim di tahun {$currentYear}.");
            return; // Hentikan pengecekan jika tahun sudah salah
        }

        // Tentukan semester saat ini dan semester sertifikat
        $currentSemester = ($currentMonth >= $ganjilStart && $currentMonth <= $ganjilEnd) ? 'Ganjil' : 'Genap';
        $certificateSemester = ($certificateMonth >= $ganjilStart && $certificateMonth <= $ganjilEnd) ? 'Ganjil' : 'Genap';

        if ($currentSemester !== $certificateSemester) {
            $fail("Klaim tidak valid. Sertifikat dari semester {$certificateSemester} tidak bisa diklaim di semester {$currentSemester}.");
        }
    }
}

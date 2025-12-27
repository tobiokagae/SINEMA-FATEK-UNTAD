<?php

namespace App\Filament\Widgets;

use App\Models\Submission;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Facades\Auth;

class StudentStatsOverview extends BaseWidget
{
    public static function canView(): bool
    {
        return Auth::user()->role === 'Student';
    }

    protected function getStats(): array
    {
        $studentId = Auth::user()->student->id;

        // Hitung total poin HANYA dari pengajuan yang sudah terverifikasi
        $totalPoints = Submission::where('student_id', $studentId)
            ->where('status', 'Verified')
            ->with('activityType') // Eager load relasi
            ->get()
            ->sum('activityType.score'); // Jumlahkan Poin dari relasi

        // Hitung Nilai Mutu
        $nilaiMutu = match (true) {
            $totalPoints > 3000 => 'A',
            $totalPoints >= 2501 => 'A-',
            $totalPoints >= 2001 => 'B+',
            $totalPoints >= 1500 => 'B',
            default => '-', // Nilai default jika di bawah 1500
        };

        return [
            Stat::make('Total Poin Terverifikasi', $totalPoints)
                ->description('Poin ekstrakurikuler yang terkumpul')
                ->descriptionIcon('heroicon-m-sparkles')
                ->color('success'),

            Stat::make('Nilai Mutu Saat Ini', $nilaiMutu)
                ->description('Berdasarkan total poin Anda')
                ->descriptionIcon('heroicon-m-star')
                ->color('info'),

            Stat::make('Pengajuan Diproses', Submission::where('student_id', $studentId)->where('status', 'Submitted')->count())
                ->description('Menunggu validasi dari verifikator')
                ->descriptionIcon('heroicon-m-clock')
                ->color('warning'),

            // Stat::make('Pengajuan Ditolak', Submission::where('student_id', $studentId)->where('status', 'Rejected')->count())
            //     ->description('Silakan periksa catatan dan perbaiki')
            //     ->descriptionIcon('heroicon-m-x-circle')
            //     ->color('danger'),
        ];
    }
}

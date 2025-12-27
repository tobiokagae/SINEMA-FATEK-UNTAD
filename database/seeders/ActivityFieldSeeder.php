<?php

namespace Database\Seeders;

use App\Models\ActivityField;
use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;

class ActivityFieldSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        $fields = [
            'Pengembangan Penalaran dan Kreativitas',
            'Kesejahteraan dan Kewirausahaan',
            'Minat, Bakat, dan Organisasi Kemahasiswaan',
            'Penyelarasan dan Pengembangan Karir',
            'Pengembangan Mental Spiritualitas Kebangsaan',
            'Internasionalisasi',
            'Pengabdian pada Masyarakat dan Lingkungan Hidup',
            'Bidang Khusus sesuai Fakultas',
        ];

        foreach ($fields as $field) {
            ActivityField::create(['name' => $field]);
        }
    }
}

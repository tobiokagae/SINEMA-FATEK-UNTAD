<?php

namespace Database\Seeders;

use App\Models\ActivityField;
use App\Models\ActivityType;
use Illuminate\Database\Seeder;

class ActivityTypeSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        // Ambil ID dari setiap bidang untuk relasi
        $penalaran = ActivityField::where('name', 'Pengembangan Penalaran dan Kreativitas')->first();
        $kesejahteraan = ActivityField::where('name', 'Kesejahteraan dan Kewirausahaan')->first();
        $minatBakat = ActivityField::where('name', 'Minat, Bakat, dan Organisasi Kemahasiswaan')->first();
        $karir = ActivityField::where('name', 'Penyelarasan dan Pengembangan Karir')->first();
        $spiritual = ActivityField::where('name', 'Pengembangan Mental Spiritualitas Kebangsaan')->first();
        $internasional = ActivityField::where('name', 'Internasionalisasi')->first();
        $pengabdian = ActivityField::where('name', 'Pengabdian pada Masyarakat dan Lingkungan Hidup')->first();
        $khusus = ActivityField::where('name', 'Bidang Khusus sesuai Fakultas')->first();

        // =========================================================================
        // TABEL 1: PENGEMBANGAN PENALARAN DAN KREATIVITAS
        // =========================================================================
        $this->generateLomba($penalaran->id, 'Memperoleh Prestasi dalam Lomba Karya Tulis Ilmiah/Naskah/Populer/Cerpen/Puisi/Opini/Sinopsis/Bussines Plan');
        $this->generateForumIlmiah($penalaran->id, 'Mengikuti Kegiatan/Forum Ilmiah (Seminar, Lokakarya, Workshop, Pameran/Poster)');
        $this->generateForumIlmiah($penalaran->id, 'Menjadi Pembicara pada Suatu Kegiatan Ilmiah', [700, 500, 300, 200, 100, 75, 50]);
        $this->generateForumIlmiah($penalaran->id, 'Menjadi Moderator pada Suatu Kegiatan Ilmiah', [600, 500, 300, 200, 100, 75, 50]);
        $this->createActivity($penalaran->id, 'Mengikuti Pelatihan/Bimbingan dalam Penyusunan Karya Tulis/Proposal', '>56 jam', null, 150);
        $this->createActivity($penalaran->id, 'Mengikuti Pelatihan/Bimbingan dalam Penyusunan Karya Tulis/Proposal', '32-56 jam', null, 100);
        $this->createActivity($penalaran->id, 'Mengikuti Pelatihan/Bimbingan dalam Penyusunan Karya Tulis/Proposal', '<32 jam', null, 50);
        $this->createActivity($penalaran->id, 'Mengikuti Seminar Proposal/Hasil Penelitian Dosen', null, null, 50);
        $this->createActivity($penalaran->id, 'Membuat karya ilmiah jurnal', 'Jurnal Internasional bereputasi', null, 700);
        $this->createActivity($penalaran->id, 'Membuat karya ilmiah jurnal', 'Jurnal Internasional', null, 600);
        $this->createActivity($penalaran->id, 'Membuat karya ilmiah jurnal', 'Jurnal Nasional Sinta 1 dan 2', null, 600);
        $this->createActivity($penalaran->id, 'Membuat karya ilmiah jurnal', 'Jurnal Nasional Sinta 3 dan 4', null, 500);
        $this->createActivity($penalaran->id, 'Membuat karya ilmiah jurnal', 'Jurnal Nasional Sinta 5 dan 6', null, 400);
        $this->createActivity($penalaran->id, 'Membuat karya ilmiah jurnal', 'Jurnal Nasional tidak terakreditasi', null, 200);
        $this->createActivity($penalaran->id, 'Menjadi Asisten Matakuliah/Praktikum/Mentor Per Semester', 'Laboratorium/Lapang', null, 250);
        $this->createActivity($penalaran->id, 'Menjadi Juri Perlombaan Olahraga, Seni dll', 'Internasional', null, 700);
        $this->createActivity($penalaran->id, 'Menjadi Juri Perlombaan Olahraga, Seni dll', 'Nasional', null, 500);
        $this->createActivity($penalaran->id, 'Menjadi Juri Perlombaan Olahraga, Seni dll', 'Regional', null, 400);
        $this->createActivity($penalaran->id, 'Menjadi Juri Perlombaan Olahraga, Seni dll', 'Universitas', null, 300);
        $this->createActivity($penalaran->id, 'Menjadi Juri Perlombaan Olahraga, Seni dll', 'Fakultas', null, 200);
        $this->generateForumIlmiah($penalaran->id, 'Duduk Sebagai Personalia Redaksi Majalah/Buletin/Surat Kabar Per Semester', [null, 500, 400, 300, 200, 100, 100]);
        $this->createActivity($penalaran->id, 'Mengikuti Kuliah Tamu', null, null, 50);
        $this->createActivity($penalaran->id, 'Mengikuti seminar proposal/hasil TA (5 kali)', null, null, 50);
        $this->generateLomba($penalaran->id, 'Sebagai Duta Mahasiswa Teladan/Berprestasi');
        $this->generateLomba($penalaran->id, 'Mengikuti Lomba (Debat, Sains, Pidato, dll)');

        // =========================================================================
        // TABEL 2: KESEJAHTERAAN DAN KEWIRAUSAHAAN
        // =========================================================================
        $this->createActivity($kesejahteraan->id, 'Mengelola Usaha/Koperasi', 'Universitas', 'Ketua', 350);
        $this->createActivity($kesejahteraan->id, 'Mengelola Usaha/Koperasi', 'Universitas', 'Wakil Ketua', 300);
        $this->createActivity($kesejahteraan->id, 'Mengelola Usaha/Koperasi', 'Universitas', 'Sekretaris', 250);
        $this->createActivity($kesejahteraan->id, 'Mengelola Usaha/Koperasi', 'Universitas', 'Wakil Sekretaris', 200);
        $this->createActivity($kesejahteraan->id, 'Mengelola Usaha/Koperasi', 'Universitas', 'Pengurus Bidang', 150);
        $this->createActivity($kesejahteraan->id, 'Mengelola Usaha/Koperasi', 'Universitas', 'Anggota Pengurus', 100);
        $this->createActivity($kesejahteraan->id, 'Mengikuti Ekspo Kewirausahaan', 'Nasional', null, 250);
        $this->createActivity($kesejahteraan->id, 'Mengikuti Ekspo Kewirausahaan', 'Regional', null, 200);
        $this->createActivity($kesejahteraan->id, 'Mengikuti Ekspo Kewirausahaan', 'Universitas', null, 150);
        $this->createActivity($kesejahteraan->id, 'Mengikuti Ekspo Kewirausahaan', 'Fakultas', null, 100);
        $this->createActivity($kesejahteraan->id, 'Berpartisipasi dalam Penanganan Bencana', 'Internasional', null, 300);
        $this->createActivity($kesejahteraan->id, 'Berpartisipasi dalam Penanganan Bencana', 'Nasional', null, 250);
        $this->createActivity($kesejahteraan->id, 'Berpartisipasi dalam Penanganan Bencana', 'Regional', null, 200);
        $this->createActivity($kesejahteraan->id, 'Berpartisipasi dalam Penanganan Bencana', 'Universitas', null, 150);
        $this->createActivity($kesejahteraan->id, 'Berpartisipasi dalam Penanganan Bencana', 'Fakultas', null, 100);

        // =========================================================================
        // TABEL 3: MINAT, BAKAT DAN ORGANISASI KEMAHASISWAAN
        // =========================================================================
        $this->generatePengurus($minatBakat->id, 'Pengurus Organisasi Keilmuan', [700, 600, 500, 400, 300, 200], [500, 400, 300, 200, 100, 75], [400, 300, 200, 100, 75, 50], [300, 200, 100, 75, 50, 25], [200, 100, 75, 50, 25, 20], [100, 75, 50, 25, 20, 15]);
        $this->generatePengurus($minatBakat->id, 'Pengurus Organisasi Non Keilmuan', [500, 400, 300, 200, 100, 75], [400, 300, 200, 100, 75, 50], [300, 200, 100, 75, 50, 25], [200, 100, 75, 50, 25, 15], [100, 75, 50, 25, 15, 10], [75, 50, 25, 15, 10, 5]);
        $this->generatePengurusBEM($minatBakat->id, 'Pengurus Organisasi Kemahasiswaan MM/BEM/UKM/UKF/HMJ/HMP');
        $this->generateLomba($minatBakat->id, 'Memperoleh Prestasi dalam Kegiatan Minat dan Bakat (Olaharaga, Seni, Tari, Drama dll)');
        $this->generatePanitia($minatBakat->id, 'Panitia dalam Suatu Kegiatan keilmuan/Non Keilmuan');
        $this->createActivity($minatBakat->id, 'Mengikuti Kegiatan yang di Surat Tugaskan oleh Rektor atau Dekan', 'Nasional', null, 200);
        $this->createActivity($minatBakat->id, 'Mengikuti Kegiatan yang di Surat Tugaskan oleh Rektor atau Dekan', 'Regional', null, 150);
        $this->createActivity($minatBakat->id, 'Mengikuti Kegiatan yang di Surat Tugaskan oleh Rektor atau Dekan', 'Universitas', null, 100);
        $this->createActivity($minatBakat->id, 'Mengikuti Kegiatan yang di Surat Tugaskan oleh Rektor atau Dekan', 'Fakultas', null, 50);
        $this->createActivity($minatBakat->id, 'Mengikuti Kegiatan berdasarkan penugasan oleh Instansi Daerah', null, null, 100);
        $this->createActivity($minatBakat->id, 'Mengikuti Kegiatan/Latihan yang Diatur oleh Masing-Masing UKM/UKF (Setiap kegiatan)', 'Universitas', null, 5);
        $this->createActivity($minatBakat->id, 'Mengikuti Kegiatan/Latihan yang Diatur oleh Masing-Masing UKM/UKF (Setiap kegiatan)', 'Fakultas', null, 3);

        // =========================================================================
        // TABEL 4: PENYELARASAN DAN PENGEMBANGAN KARIER
        // =========================================================================
        $this->createActivity($karir->id, 'Mengikuti Pelatihan/Kursus Peningkatan Sumber Daya Manusia (SAR/Pramuka/Menwa dll)', 'Internasional', null, 700);
        $this->createActivity($karir->id, 'Mengikuti Pelatihan/Kursus Peningkatan Sumber Daya Manusia (SAR/Pramuka/Menwa dll)', 'Nasional', null, 500);
        $this->createActivity($karir->id, 'Mengikuti Pelatihan/Kursus Peningkatan Sumber Daya Manusia (SAR/Pramuka/Menwa dll)', 'Regional', null, 400);
        $this->createActivity($karir->id, 'Mengikuti Pelatihan/Kursus Peningkatan Sumber Daya Manusia (SAR/Pramuka/Menwa dll)', 'Universitas', null, 300);
        $this->createActivity($karir->id, 'Mengikuti Pelatihan Kepemimpinan LKMM', 'Lanjut', null, 400);
        $this->createActivity($karir->id, 'Mengikuti Pelatihan Kepemimpinan LKMM', 'Menengah', null, 300);
        $this->createActivity($karir->id, 'Mengikuti Pelatihan Kepemimpinan LKMM', 'Dasar', null, 200);
        $this->createActivity($karir->id, 'Mengikuti kegiatan kepemimpinan lainnya', null, null, 100);
        $this->generateForumIlmiah($karir->id, 'Mengikuti Seminar/Workshop/Lokakarya/Diskusi', [700, 500, 400, 300, 200, 150, 100]);
        $this->createActivity($karir->id, 'Mengikuti kegiatan PKKMB', null, null, 150);
        $this->createActivity($karir->id, 'Duta Kampus', 'Internasional', null, 700);
        $this->createActivity($karir->id, 'Duta Kampus', 'Nasional', null, 500);
        $this->createActivity($karir->id, 'Duta Kampus', 'Regional', null, 400);
        $this->createActivity($karir->id, 'Duta Kampus', 'Universitas', null, 300);

        // =========================================================================
        // TABEL 5: PENGEMBANGAN MENTAL SPIRITUALITAS KEBANGSAAN
        // =========================================================================
        $this->createActivity($spiritual->id, 'Mengikuti Kegiatan Keagamaan, Kebangsaan, dan Sosial Budaya', 'Internasional', null, 400);
        $this->createActivity($spiritual->id, 'Mengikuti Kegiatan Keagamaan, Kebangsaan, dan Sosial Budaya', 'Nasional', null, 300);
        $this->createActivity($spiritual->id, 'Mengikuti Kegiatan Keagamaan, Kebangsaan, dan Sosial Budaya', 'Regional', null, 200);
        $this->createActivity($spiritual->id, 'Mengikuti Kegiatan Keagamaan, Kebangsaan, dan Sosial Budaya', 'Universitas', null, 100);
        $this->createActivity($spiritual->id, 'Mengikuti Kegiatan Keagamaan, Kebangsaan, dan Sosial Budaya', 'Fakultas', null, 75);
        $this->createActivity($spiritual->id, 'Mengikuti Upacara Bendera dan Upacara Hari-hari Besar Nasional minimal 3 (Tiga) Kali', null, null, 75);
        $this->createActivity($spiritual->id, 'Mengikuti kegiatan Keagamaan dan Kebangsaan Secara Rutin minimal 10 Kali', null, null, 50);

        // =========================================================================
        // TABEL 6: INTERNASIONALISASI
        // =========================================================================
        $this->createActivity($internasional->id, 'Mengikuti Pertukaran Mahasiswa dan kegiatan internasional lainnya', 'Internasional', null, 700);

        // =========================================================================
        // TABEL 7: PENGABDIAN PADA MASYARAKAT DAN LINGKUNGAN HIDUP
        // =========================================================================
        $this->createActivity($pengabdian->id, 'Berpartisipasi dalam Duta Lingkungan', 'Internasional', null, 400);
        $this->createActivity($pengabdian->id, 'Berpartisipasi dalam Duta Lingkungan', 'Nasional', null, 300);
        $this->createActivity($pengabdian->id, 'Berpartisipasi dalam Duta Lingkungan', 'Regional', null, 200);
        $this->createActivity($pengabdian->id, 'Berpartisipasi dalam Duta Lingkungan', 'Universitas', null, 100);
        $this->createActivity($pengabdian->id, 'Mengikuti Kegiatan Bakti Kampus', null, null, 25);
        $this->createActivity($pengabdian->id, 'Mengikuti Kegiatan Bakti Sosial', null, null, 50);
        $this->createActivity($pengabdian->id, 'Mengikuti Kegiatan Bakti Lingkungan', null, null, 50);
        $this->createActivity($pengabdian->id, 'Melakukan Pengabdian/Penyuluhan Pada Masyarakat', null, null, 100);

        // =========================================================================
        // TABEL 8: BIDANG KHUSUS FAKULTAS
        // =========================================================================
        $this->createActivity($khusus->id, 'Contoh: Kegiatan Khas Fakultas Teknik', 'Fakultas', 'Peserta', 50);
    }

    /**
     * Helper function to create an activity type.
     */
    private function createActivity(int $fieldId, string $name, ?string $level, ?string $achievement, int $score): void
    {
        ActivityType::create([
            'activity_field_id' => $fieldId,
            'name' => $name,
            'level' => $level,
            'achievement' => $achievement,
            'score' => $score,
        ]);
    }

    /**
     * Helper function to generate standard competition entries.
     */
    private function generateLomba(int $fieldId, string $name): void
    {
        $levels = [
            'Internasional' => [[700, 600, 500], 400, 300],
            'Nasional' => [[500, 400, 300], 200, 100],
            'Regional' => [[300, 200, 150], 100, 75],
            'Universitas' => [[200, 150, 100], 75, 50],
            'Fakultas' => [[150, 100, 75], 50, 25],
            'Jurusan' => [[75, 50, 25], 20, 15],
            'Program Studi' => [[75, 50, 25], 20, 15],
        ];
        $achievements = ['Juara I', 'Juara II', 'Juara III'];

        foreach ($levels as $levelName => $scores) {
            foreach ($achievements as $index => $achievementName) {
                $this->createActivity($fieldId, $name, $levelName, $achievementName, $scores[0][$index]);
            }
            $this->createActivity($fieldId, $name, $levelName, 'Favorit', $scores[1]);
            $this->createActivity($fieldId, $name, $levelName, 'Peserta', $scores[2]);
        }
    }

    /**
     * Helper function to generate scientific forum entries.
     */
    private function generateForumIlmiah(int $fieldId, string $name, array $scores = [600, 500, 300, 200, 100, 75, 50]): void
    {
        $levels = ['Internasional', 'Nasional', 'Regional', 'Universitas', 'Fakultas', 'Jurusan', 'Program Studi'];
        foreach ($levels as $index => $levelName) {
            if (isset($scores[$index])) {
                $this->createActivity($fieldId, $name, $levelName, null, $scores[$index]);
            }
        }
    }

    /**
     * Helper function to generate committee member entries.
     */
    private function generatePengurus(int $fieldId, string $name, array $int, array $nas, array $reg, array $univ, array $fak, array $jur): void
    {
        $roles = ['Ketua', 'Wakil Ketua', 'Sekretaris', 'Wakil Sekretaris', 'Pengurus Bidang', 'Anggota Pengurus'];
        $levels = [
            'Internasional' => $int,
            'Nasional' => $nas,
            'Regional' => $reg,
            'Universitas' => $univ,
            'Fakultas' => $fak,
            'Jurusan/Program Studi/Bidang' => $jur
        ];
        foreach ($levels as $levelName => $scores) {
            foreach ($roles as $index => $roleName) {
                $this->createActivity($fieldId, $name, $levelName, $roleName, $scores[$index]);
            }
        }
    }

    private function generatePengurusBEM(int $fieldId, string $name): void
    {
        $roles = ['Ketua', 'Wakil Ketua', 'Sekretaris', 'Wakil Sekretaris', 'Bendahara', 'Wakil Bendahara', 'Ketua Pengurus Bidang', 'Anggota Pengurus'];
        $levels = [
            'Universitas' => [500, 400, 300, 200, 300, 200, 100, 75],
            'Fakultas' => [400, 300, 200, 100, 200, 100, 75, 50],
            'Jurusan/Prodi/Bagian' => [300, 200, 100, 75, 100, 75, 50, 25]
        ];
        foreach ($levels as $levelName => $scores) {
            foreach ($roles as $index => $roleName) {
                $this->createActivity($fieldId, $name, $levelName, $roleName, $scores[$index]);
            }
        }
    }

    private function generatePanitia(int $fieldId, string $name): void
    {
        $roles = ['Ketua', 'Wakil Ketua', 'Sekretaris', 'Wakil Sekretaris', 'Bendahara', 'Wakil Bendahara', 'Anggota'];
        $levels = [
            'Nasional' => [100, 75, 75, 50, 75, 50, 50],
            'Universitas' => [75, 50, 50, 25, 50, 25, 15],
            'Fakultas' => [50, 25, 25, 15, 25, 15, 10],
            'Jurusan/Prodi' => [25, 15, 15, 10, 15, 10, 5]
        ];
        foreach ($levels as $levelName => $scores) {
            foreach ($roles as $index => $roleName) {
                if (isset($scores[$index])) {
                    $this->createActivity($fieldId, $name, $levelName, $roleName, $scores[$index]);
                }
            }
        }
    }
}

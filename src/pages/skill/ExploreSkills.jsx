// This is the main page where users can browse all available skills

import { useState } from 'react';
import SkillCard from '../../components/skill/SkillCard';

// the data (hardcoded for now -  l connect to Pasha's backend later)
const sampleSkills = [
    { id: 1, name: 'Prompt Engineering', category: 'IT', description: 'Learn how to write effective prompts for AI models' },
    { id: 2, name: 'Financial Analysis', category: 'Business', description: 'Read and interpret financial statements' },
    { id: 3, name: 'Web Development', category: 'IT', description: 'Build websites with HTML, CSS, and JavaScript' },
    { id: 4, name: 'Public Speaking', category: 'Communication', description: 'Improve your confidence and speaking skills' },
    { id: 5, name: 'Graphic Design', category: 'Design', description: 'Create stunning visuals with Canva and Photoshop' },
];

const ExploreSkills = () => {
    // State to store the search term
    const [searchTerm, setSearchTerm] = useState('');

    // Filter skills based on search term
    const filteredSkills = sampleSkills.filter(skill =>
        skill.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        skill.category?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
            <h1 style={{ fontSize: '32px', color: '#1a1a2e' }}>
                🔍 Explore Skills
            </h1>
            <p style={{ color: '#666', marginBottom: '20px' }}>
                Find skills to learn or teach. Search by name or category.
            </p>

            {/* Search Bar */}
            <input
                type="text"
                placeholder="Search for a skill..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    fontSize: '16px',
                    marginBottom: '20px',
                    boxSizing: 'border-box'
                }}
            />

            {/* Skills Grid */}
            <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center' }}>
                {filteredSkills.length === 0 ? (
                    <p>No skills found. Try a different search.</p>
                ) : (
                    filteredSkills.map((skill) => (
                        <SkillCard key={skill.id} skill={skill} />
                    ))
                )}
            </div>
        </div>
    );
};

export default ExploreSkills;

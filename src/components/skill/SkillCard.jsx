// This is a single skill card that shows up in the list
// It displays the skill name, category, and a "Request Swap" button

const SkillCard = ({ skill }) => {
    return (
        <div style={{
            border: '1px solid #ddd',
            borderRadius: '12px',
            padding: '16px',
            margin: '10px',
            backgroundColor: 'white',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            width: '250px',
            display: 'inline-block'
        }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#1a1a2e' }}>
                {skill.name}
            </h3>
            {skill.category && (
                <span style={{
                    backgroundColor: '#e0f2fe',
                    color: '#0369a1',
                    padding: '2px 10px',
                    borderRadius: '20px',
                    fontSize: '12px',
                    display: 'inline-block'
                }}>
                    {skill.category}
                </span>
            )}
            <p style={{ color: '#666', fontSize: '14px', margin: '10px 0' }}>
                {skill.description || 'No description provided.'}
            </p>
            <button style={{
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '8px',
                cursor: 'pointer',
                width: '100%',
                fontSize: '14px'
            }}>
                🔄 Request Swap
            </button>
        </div>
    );
};

export default SkillCard;